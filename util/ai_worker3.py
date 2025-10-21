import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from datetime import date, timedelta

from pydantic import BaseModel, Field
from typing import Optional, List
from pathlib import Path
import json

load_dotenv()
OPENAI_KEY =  os.getenv("OPENAI_API_KEY")

def get_llm_instance(model = "gpt-4o-mini", temperature = 0.5):
    llm = ChatOpenAI(
    model=model,
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

months_with_indentation = {'01': '  JANUARY', '02': ' FEBRUARY', '03': '    MARCH', '04': '    APRIL',
 '05': '      MAY', '06': '     JUNE', '07': '     JULY', '08': '   AUGUST',
 '09': 'SEPTEMBER', '10': '  OCTOBER', '11': ' NOVEMBER', '12': ' DECEMBER'}

# Pydentic model to get the weekahead row data.
class RowData(BaseModel):
    month: str
    day: str
    year: str
    prev_month: int
    prev_day: str
    prev_year: str
    week: str
    prevJulday: str
    curJulday: str
    isFirstWeekOfMonth: bool = False
    isLastWeekOfMonth: bool = False
    financialYearMonth: int = 0



# Pydantic Model for Prompt
class PromptStructure(BaseModel):
    topic: Optional[str] = None
    objective: Optional[str] = None
    input: Optional[str] = None
    output: Optional[str] = None      # include JSON-only constraint here
    example: Optional[str] = None
    rulesAlgorithm: Optional[str] = None
    renderingContract: Optional[str] = None  # not used now but keep if you want
    constants: Optional[str] = None
    contextHints: Optional[str] = None


# Supporiting function for building the final prompt.
def build_prompt(builder: PromptStructure):
    template = """
    You are a meticulous schedule generator.

    Topic:
    {topic}

    Objective:
    {objective}

    Input:
    {input}

    Output (JSON-only, UTF-8 safe, no markdown fences, no prose):
    {output}

    Example (shape intuition; do NOT copy values):
    {example}

    Rules & Algorithm (MUST follow exactly):
    {rulesAlgorithm}

    Constants (DO NOT alter):
    {constants}

    Context Hints:
    {contextHints}
    """
    return PromptTemplate.from_template(template).partial(
        topic=builder.topic or "",
        objective=builder.objective or "",
        input=builder.input or "",
        output=builder.output or "",
        example=builder.example or "",
        rulesAlgorithm=builder.rulesAlgorithm or "",
        constants=builder.constants or "",
        contextHints=builder.contextHints or "",
    )

    
# Define each aspect of the prompt following the Prompt Structure
def prompt_structure_builder(year: int):
    first_date = get_first_date_of_financial_year(year)
    last_date = get_second_last_date_of_financial_year(year)
    
    topic = f"Generate weekly Thursday rows for financial year {year}."

    objective = (
        f"Compute all Thursdays from {first_date} through {last_date} inclusive. "
        "For each Thursday, produce a JSON object matching the RowData schema."
    )

    input_ = (
        "Inputs: {year, first_date, last_date}. You must compute sequence, week numbering, "
        "financial year month (per rule below), A/L boundaries, and Julian days."
    )

    # Output: JSON array only, strict keys
    output = """
    Return ONLY a valid JSON array (no surrounding text). Each element MUST have EXACTLY these keys with types:
    [
    {
        "month": "<2-digit string MM>",
        "day": "<2-digit string DD>",
        "year": "<4-digit string YYYY>",
        "prev_month": "<2-digit string MM>",
        "prev_day": "<2-digit string DD>",
        "prev_year": "<4-digit string YYYY>",
        "week": "<2-digit string WW>",
        "prevJulday": "<3-digit string JJJ>",
        "curJulday": "<3-digit string JJJ>",
        "isFirstWeekOfMonth": <True|False>,
        "isLastWeekOfMonth": <True|False>,
        "financialYearMonth": <int 1..12>
    },
    ...
    ]
    """.strip()

    example = """
    [
    {
        "month": "12",
        "day": "26",
        "year": "2024",
        "prev_month": "12",
        "prev_day": "19",
        "prev_year": "2024",
        "week": "01",
        "prevJulday": "354",
        "curJulday": "361",
        "isFirstWeekOfMonth": True,
        "isLastWeekOfMonth": False,
        "financialYearMonth": 1
    }
    ]
    """.strip()

    rulesAlgorithm = f"""
    1) Thursdays list: start at first_date = {first_date}; end at last_date = {last_date}; step +7 days (inclusive).
    2) For each current_date:
    - prev_date = current_date - 7 days
    - week = sequential 1-based index, zero-padded "WW"
    - financialYearMonth (int):
        * Dec({year-1}) -> 1 ; Jan({year}) -> 1
        * Feb..Nov({year}) -> 2..11
        * Dec({year}) -> 12
    - isFirstWeekOfMonth / isLastWeekOfMonth:
        * TRUE only at financial-month boundaries: first row of group => isFirstWeekOfMonth=True; last row => isLastWeekOfMonth=True.
        * Interior rows both False.
    - month = calendar month number of current_date (1..12)
    - day = "DD" ; year = "YYYY"
    - prev_month, prev_day, prev_year from prev_date (month/day/year as strings formatted "MM", "DD", "YYYY")
    - prevJulday = DOY(prev_date) as 3-digit string (001..366) [ex: Jan 01 => 001, Jan 05 => 005 and so-on], can use datetime.timetuple().tm_yday
    - curJulday  = DOY(current_date) as 3-digit string (001..366) [ex: Jan 01 => 001, Jan 05 => 005 and so-on], can use datetime.timetuple().tm_yday
    3) IMPORTANT:
    - Output must be STRICT JSON (a single array). No comments, no trailing commas, no markdown.
    - Keys and value types must match exactly as specified.
    - While calculating Julian Date keep in mind for Leap year (e.g:2020, 2024, 2028,...) Feb month have 29 days make no mistake in julain-date calculation.
    """

    constants = (
        f"year: {year}\n"
        f"first_date: {first_date}\n"
        f"last_date:  {last_date}\n"
        "months_with_indentation: provided separately; DO NOT compute indentation here (rendering uses it later)."
    )

    contextHints = """
    - Do not attempt fixed-width rendering here. Only compute fields needed for RowData.
    - Financial-month boundary rule: (Dec prev + Jan curr) is month=1; interior months follow 2..12; last month (Dec curr)=12.
    - Common pitfalls: off-by-one on julian days; not zero-padding strings; setting first line to financialMonth=12 (WRONG: must be 1).
    """.strip()

    return PromptStructure(
        topic=topic,
        objective=objective,
        input=input_,
        output=output,
        example=example,
        rulesAlgorithm=rulesAlgorithm.strip(),
        renderingContract="",      # not used here
        constants=constants.strip(),
        contextHints=contextHints,
    )

# Transformation function takes RowData and return the list of string
def get_file_utf(rows: RowData):
    lst_str: List[str] = []

    for row in rows:
        s = []
        s.append(months_with_indentation[row.month])
        s.append(" ")
        s.append(str(row.day))
        s.append(" ")
        s.append(str(row.year))
        s.append(" "*2)
        s.append(str(row.week))
        s.append(" "*2)
                
        if row.isFirstWeekOfMonth:
            s.append("A")
        elif row.isLastWeekOfMonth:
            s.append("L")
        else:
            s.append(" ")
        s.append(f"{row.financialYearMonth:02d}")
        
        s.append(" "*22)
        s.append(str(row.prev_year))
        s.append(str(row.prevJulday))
        s.append(str(row.year))
        s.append(str(row.curJulday))
        s.append(" "*2)
        s.append(str(row.prev_year))
        s.append(f"{row.prev_month:02d}")
        # s.append(str(row.prev_month))
        s.append(str(row.prev_day))
        s.append(str(row.year))
        s.append(str(row.month))
        # s.append(f"{row.month:02d}")
        s.append(str(row.day))
                
        lst_str.append("".join(s))
    return lst_str



# Transformation function: return a langchain
def chain_llm_with_prompt(year: int):
    # Get the instance of prompt structure
    prompt_strt = prompt_structure_builder(year)
    # Generate the prompt as blob text
    prompt_template = build_prompt(prompt_strt)
    # Get LLM instance
    llm = get_llm_instance(model="gpt-5-mini")
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
    rows_json = json.loads(text)
    rows: list[RowData] = [RowData(**d) for d in rows_json]
    text = "\n".join(get_file_utf(rows))
    return text

def file_generator(year, text):
    out_path = Path(f"financial_year_{year}_output.txt")
    out_path.write_text(text, encoding="utf-8")
    print(f"\n File saved successfully: {out_path.resolve()}")

def controller(year):
    text = chain_llm_with_prompt(year)
    return text.encode("utf-8")
