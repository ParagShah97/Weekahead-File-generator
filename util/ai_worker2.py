import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from datetime import date, timedelta

from pydantic import BaseModel, Field
from typing import Optional, List
from pathlib import Path

load_dotenv()
OPENAI_KEY =  os.getenv("OPENAI_API_KEY")

def get_llm_instance(model = "gpt-4o-mini", temperature = 0.4):
    llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=OPENAI_KEY,
    temperature=temperature,
    streaming=False,
    )
    return llm

def get_first_date_of_financial_year(year):
    d = date(year - 1, 12, 31)          # Dec 31 of previous year
    # print(d.weekday())
    offset = (d.weekday() - 3) % 7      # Thursday = 3 (Mon=0..Sun=6)
    return d - timedelta(days=offset)

def get_second_last_date_of_financial_year(year):
    d = date(year, 12, 31)                    # Dec 31 of the same year
    last_thu = d - timedelta(days=(d.weekday() - 3) % 7)  # last Thursday
    return last_thu - timedelta(days=7)       # second-to-last Thursday

months_with_indentation = {1: '  JANUARY', 2: ' FEBRUARY', 3: '    MARCH', 4: '    APRIL',
 5: '      MAY', 6: '     JUNE', 7: '     JULY', 8: '   AUGUST',
 9: 'SEPTEMBER', 10: '  OCTOBER', 11: ' NOVEMBER', 12: ' DECEMBER'}


# Pydantic Model for Prompt
class PromptStructure(BaseModel):
    # Core
    topic: Optional[str] = None
    objective: Optional[str] = None
    input: Optional[str] = None
    output: Optional[str] = None  # include final constraints here
    example: Optional[str] = None

    # Merged / essential controls
    rulesAlgorithm: Optional[str] = None          # rules + algorithm combined
    renderingContract: Optional[str] = None       # strict 80-char layout
    constants: Optional[str] = None               # year, month map, first/last dates
    contextHints: Optional[str] = None            # context + validator hints merged

# Supporiting function for building the final prompt.
def build_prompt(builder: PromptStructure):
    template = """
        You are a professional schedule file generator. Create a file consisting of dates and other information.
        Produce ONLY the final lines—no commentary.

        Topic:
        {topic}

        Objective:
        {objective}

        Input:
        {input}

        Output (includes hard constraints):
        {output}

        Example (format intuition; DO NOT copy content):
        {example}

        Rules & Algorithm (MUST follow exactly):
        {rulesAlgorithm}

        Rendering Contract (80 chars per line; field-by-field spec):
        {renderingContract}

        Constants (DO NOT alter):
        {constants}

        Context Hints (domain specifics + common error traps to avoid):
        {contextHints}
        """
    
    return PromptTemplate.from_template(template).partial(
        topic=builder.topic or "",
        objective=builder.objective or "",
        input=builder.input or "",
        output=builder.output or "",
        example=builder.example or "",
        rulesAlgorithm=builder.rulesAlgorithm or "",
        renderingContract=builder.renderingContract or "",
        constants=builder.constants or "",
        contextHints=builder.contextHints or "",
    )

    
# Define each aspect of the prompt following the Prompt Structure
def prompt_structure_builder(year: int):
    first_date = get_first_date_of_financial_year(year)
    last_date = get_second_last_date_of_financial_year(year)
    months_map = "\n".join([f"{k}:{v}" for k, v in months_with_indentation.items()])

    topic = f"Generate a financial-year weekly schedule for {year} (Thursdays only)."

    objective = (
        f"Compute all Thursdays from {first_date} through {last_date} inclusive, then "
        "render strict fixed-width lines (80 chars) per the contract."
    )

    input_ = (
        "Inputs provided: year, months_with_indentation map, first_date, last_date. "
        "You must compute the sequence, week numbers, financial-month index, A/L flags, julian day fields, "
        "and render the final lines exactly as specified."
    )

    # Output now includes constraints
    output = (
        "Return ONLY the final lines (UTF-8 safe). No quotes, no commentary, no extra whitespace. "
        "Output exactly N lines (N = number of Thursdays from first_date..last_date inclusive). "
        "EVERY line must be exactly 80 characters."
    )

    example = (
        "FORMAT SHAPE EXAMPLE (illustrative; do NOT copy dates):\n"
        " DECEMBER 26 2024  01  A01                      20243542024361  2024121920241226\n"
        "  JANUARY 02 2025  02   01                      20243612025002  2024122620250102\n"
        "  JANUARY 09 2025  03   01                      20250022025009  2025010220250109\n"
        "  JANUARY 16 2025  04   01                      20250092025016  2025010920250116\n"
        "  JANUARY 23 2025  05   01                      20250162025023  2025011620250123\n"
        "  JANUARY 30 2025  06  L01                      20250232025030  2025012320250130\n"
        " FEBRUARY 06 2025  07  A02                      20250302025037  2025013020250206\n"
        " FEBRUARY 13 2025  08   02                      20250372025044  2025020620250213\n"
        " FEBRUARY 20 2025  09   02                      20250442025051  2025021320250220\n"
        " FEBRUARY 27 2025  10  L02                      20250512025058  2025022020250227\n"
    )

    # === KEY FIXES: make fin-month mapping and A/L boundaries unambiguous ===
    rulesAlgorithm = f"""
    1) Build the Thursday list:
    - Start at first_date = {first_date}; end at last_date = {last_date}; step +7 days (inclusive).

    2) For each current_date:
    - prev_date = current_date - 7 days
    - week_number = 1-based index (zero-pad: 01, 02, ...)
    - financial month (2-digit) MUST use this lookup (DO NOT infer from calendar month):
        if (current_date.year == {year}-1 and month == 12): "01"
        elif (current_date.year == {year} and month == 1):  "01"
        elif (current_date.year == {year} and 2 <= month <= 11): f"{{month:02d}}"  # 02..11
        elif (current_date.year == {year} and month == 12): "12"
        else:  ERROR (should not occur)
    - A/L flags apply ONLY at financial-month group boundaries:
        * First row of a financial-month group -> "Axx" (xx = that group's fin-month)
        * Last  row of that group             -> "Lxx"
        * Rows strictly inside the group      -> one single space " "
        IMPORTANT: Do NOT toggle flags week-by-week. Flags appear ONLY on the first and last rows of each group.

    3) Month label:
    - month_label := months_with_indentation[current_date.month]
    - Treat month_label as an opaque string. Do NOT trim or normalize spaces. Copy EXACTLY.

    4) Julian days (3-digit):
    - prev_jul := day-of-year(prev_date) formatted 3 digits (001..366)
    - cur_jul  := day-of-year(current_date) formatted 3 digits (001..366)

    5) Golden boundary checks (MUST be true for year {year}):
    - The very first line (for {first_date}) MUST have flag "A01" and fin_month "01".
    - The very last line (for {last_date})  MUST have flag "L12" and fin_month "12".
    """

    renderingContract = """
    Concatenate in this exact order (final line length MUST be 80):

    1) month_label
    2) " "
    3) day (DD)
    4) " "
    5) year (YYYY)
    6) "  "
    7) week_number (WW)
    8) "  "
    9) flag_field ("Axx"/"Lxx"/" ")
    10) fin_month (MM)
    11) " " * 22
    12) prev_year + prev_jul (YYYY + JJJ)
    13) year + cur_jul       (YYYY + JJJ)
    14) "  "
    15) prev_year + prev_month + prev_day (YYYY + MM + DD)
    16) year + current_day + current_month (YYYY + DD + MM)
    """

    constants = (
        f"year: {year}\n"
        "months_with_indentation (DO NOT alter):\n"
        f"{months_map}\n\n"
        f"first_date: {first_date}\n"
        f"last_date:  {last_date}"
    )

    # Context + common traps merged
    contextHints = """
    - December (previous year) and January (current year) are BOTH financial month "01".
    - Feb..Nov are "02".."11"; December (current) is "12".
    - Use month_label exactly as provided (opaque string). Never trim leading spaces.
    - Flags ONLY at group boundaries: first -> Axx, last -> Lxx, interior -> single space.
    - Common pitfalls to avoid:
    * Setting "A12" for the first line at the year boundary. It MUST be "A01".
    * Toggling A/L weekly instead of only at boundaries.
    * Forgetting the 22 spaces after the financial-month field.
    * Emitting 79 or 81 characters due to missing/extra spaces.
    * Copying the illustrative example’s dates verbatim.
    """.strip()

    return PromptStructure(
        topic=topic,
        objective=objective,
        input=input_,
        output=output,
        example=example,
        rulesAlgorithm=rulesAlgorithm.strip(),
        renderingContract=renderingContract.strip(),
        constants=constants.strip(),
        contextHints=contextHints,
    )



# Transformation function: return a langchain
def chain_llm_with_prompt(year):
    prompt_strt = prompt_structure_builder(year)
    prompt_template = build_prompt(prompt_strt)
    llm = get_llm_instance()
    chain = prompt_template | llm | StrOutputParser()
    first_date = get_first_date_of_financial_year(year)
    last_date = get_second_last_date_of_financial_year(year)
    supporting_vars = {
        "year": year,
        "months_with_indentation": months_with_indentation,
        "first_date": first_date,
        "last_date": last_date        
    }
    # print("The chain is", chain)
    text = chain.invoke(supporting_vars)
    print(text)
    
    out_path = Path(f"financial_year_{year}_output.txt")
    out_path.write_text(text, encoding="utf-8")
    print(f"\n✅ File saved successfully: {out_path.resolve()}")
    # pass

def file_generator():
    pass

def controller(year):
    pass

def main():
    # prompt_structure_builder(2025)
    chain_llm_with_prompt(2025)

if __name__ == "__main__":
    main()