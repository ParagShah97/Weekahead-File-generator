import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from datetime import date, timedelta

from pydantic import BaseModel, Field
from typing import Optional, List

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
    topic: Optional[str] = Field(None, description="The main idea about the usecase.")
    objective: Optional[str] = Field(None, description="Defination about the task, and detailed information what need to be done.")
    input: Optional[str] = Field(None, description="Define input format, provided by the user.")
    output: Optional[str] = Field(None, description="Define output format, required by the user.")
    contextInfo: Optional[str] = Field(None, description="More information, like domain knowledge or background about the use case.")
    rules: Optional[str] = Field(None, description="All the rules or constraints to achieve the object over the input to get the required output.")
    example: Optional[str] = Field(None, description="Supporting example either on how to achieve the objective or how the output looks like after applying the rules.")

# Supporiting function for building the final prompt.
def build_prompt(builder: PromptStructure):
    template = """
    You are a professional schedule file generator, your task is to create a file content which consist of dates and other information, 
    follow all the instruction properly and provide desired output. Don't add additional commentry, just give the output in the right format,
    confirm with the example.
    
    Topic:
    {topic}
    
    Objective:
    {objective}
    
    Input:
    {input}
    
    Output:
    {output}
    
    Context and additional details:
    {contextInfo}
    
    Rules: (Strictly follow)
    {rules}
    
    Example: (Keep the examples in mind)
    {example}
    """
    
    return PromptTemplate.from_template(template=template).partial(
        topic = builder.topic or "",
        objective = builder.objective or "",
        input = builder.input or "",
        output = builder.output or "",
        contextInfo = builder.contextInfo or "",
        rules = builder.rules or "",
        example = builder.example or ""
    )
    
# Define each aspect of the prompt following the Prompt Structure
def prompt_structure_builder(year):
    
    first_date = get_first_date_of_financial_year(year)
    last_date = get_second_last_date_of_financial_year(year)
    
    topic = f"""
    Generating a weekahead file which have the records for all the thrusdays in a financial year starting from previous year december last thrusday and go till second last thrusday of current year december.
    """
    
    objective = f"""
    Need to create a txt file from the date {first_date} till the date {last_date}, all the dates should be of Thursday of every week.
    """
    
    input =f"""
    First ({first_date}) and last ({last_date}) dates.
    """
    
    output = f"""
    return the file in utf-8 format which then stored in the txt file.
    """
    
    rules = f"""
    Below is the primary rules, need to strictly follow that there are 80 character column and all the row will be having exactly 80 column characters.
    
    Indentation + month (ex: December,January,...) [column 1-9] + " "*1 + date (ex-01,12,31) [column 11-12] + " "*1 + Year (ex-2023,2025,2026)[Column 14-17] 
    + " "*2 [column 18-19] + week_number(ex - 01-52) [column 20-21] + " "*2 [column 22-23] + A/L-week_number (first week of month-A last week of month-L ex-  A12,L01,A02) [columns 24-26] 
    + " "*22 [columns 27-48] + Year(previous date year delta of -7 ex- 2025,2026, ...) [column 49-52] + ___(three digit of prev days of year, just previous date ex January 01, 02 equals 001, 002 and so-on) [column 53-55] 
    + Year (curent year ex-2024,2025) [column 56-59] + day_number_of_year (three digit of current day of year ex January 01, 02 equals 001, 002 and so-on) [column 60-62] + " "*2 [column 63-64] 
    + previous_date_Year (previous date year delta = -7 ex-2024,2025) [column 65-68] + previous_date_month (previous date month delta = -7 ex-01,02,03...) [column 69-70]
    + previou_date_day (previous date day delta=-7 ex-01,02,14,31...) [column 71-72] + current_Year (current date year ex-2024,2025) [column 73-76]
    + Month (current date month ex-01,02,03...) [column 77-78] + date (current date day ex-01,02,14,31...) [column 79-78]
    
    You need to add the indetation to make the lenght of all the months same you can use {months_with_indentation}, i.e adding extra space if month name character is smaller
     
    For A and L logic, it work over the financial year the first month includes last month of december of previous year till last week of january, so A12 and L01
    there won't be A01 as first week of january will called as second week of financial year. Similarly second last week of cuurent year december will be
    last week therefore L12 for last row.   
    """
    contextInfo  = f"""
    Strictly follow all the rules.
    """
    example = f"""
    
    For financial year 2025:
    
    " DECEMBER 26 2024  01  A01                      20243542024361  2024121920241226"
    "  JANUARY 02 2025  02   01                      20243612025002  2024122620250102"
    "  JANUARY 09 2025  03   01                      20250022025009  2025010220250109"
    "  JANUARY 16 2025  04   01                      20250092025016  2025010920250116"
    "  JANUARY 23 2025  05   01                      20250162025023  2025011620250123"
    "  JANUARY 30 2025  06  L01                      20250232025030  2025012320250130"
    " FEBRUARY 06 2025  07  A02                      20250302025037  2025013020250206"
    " FEBRUARY 13 2025  08   02                      20250372025044  2025020620250213"
    " FEBRUARY 20 2025  09   02                      20250442025051  2025021320250220"
    " FEBRUARY 27 2025  10  L02                      20250512025058  2025022020250227"

    in the output don't include the double quotes, they are just to show the indentation and all rows have 80 character (columns) each.
    """
    
    prompt_builder = PromptStructure(topic=topic, objective=objective, input=input, output=output, contextInfo=contextInfo, rules=rules, example=example)
    return prompt_builder

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
    pass

def file_generator():
    pass

def controller(year):
    pass

def main():
    # prompt_structure_builder(2025)
    chain_llm_with_prompt(2025)

if __name__ == "__main__":
    main()