from datetime import date, timedelta
from pydantic import BaseModel
from datetime import timedelta
from pathlib import Path

def get_first_date_of_financial_year(year):
    d = date(year - 1, 12, 31)          # Dec 31 of previous year
    print(d.weekday())
    offset = (d.weekday() - 3) % 7      # Thursday = 3 (Mon=0..Sun=6)
    return d - timedelta(days=offset)

def get_second_last_date_of_financial_year(year):
    d = date(year, 12, 31)                    # Dec 31 of the same year
    last_thu = d - timedelta(days=(d.weekday() - 3) % 7)  # last Thursday
    return last_thu - timedelta(days=7)       # second-to-last Thursday

months_with_indentation = {1: '  JANUARY', 2: ' FEBRUARY', 3: '    MARCH', 4: '    APRIL',
 5: '      MAY', 6: '     JUNE', 7: '     JULY', 8: '   AUGUST',
 9: 'SEPTEMBER', 10: '  OCTOBER', 11: ' NOVEMBER', 12: ' DECEMBER'}


class RowData(BaseModel):
    month: int
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
    
def row_data_for_file(year):
    first_date = get_first_date_of_financial_year(year)
    last_date = get_second_last_date_of_financial_year(year)
    day_before_first_day = first_date - timedelta(days=7)
    curr = first_date
    week = 1  # start at 1 (not 01)
    rows: list[RowData] = []
    
    while curr <= last_date:
        prev = curr - timedelta(days=7)
        isFirstWeekOfMonth = False
        # First financial year week will be previous year last week in december.
        if rows == []:
            # Last week of December, but first week of Financial month
            isFirstWeekOfMonth = True
        # New month (when previous month is different from current month)
        # but not January (which is financial month 1)
        elif curr.month != rows[-1].month and curr.month != 1:
            isFirstWeekOfMonth = True
            rows[-1].isLastWeekOfMonth = True
        
        financialYearMonth = 0
        if curr.month == 12 and curr.year == year-1:
            financialYearMonth = 1
        else:
            financialYearMonth = curr.month

        row = RowData(
            month=curr.month,
            day=f"{curr.day:02d}",
            year=str(curr.year),

            prev_month=prev.month,
            prev_day=f"{prev.day:02d}",
            prev_year=str(prev.year),

            week=f"{week:02d}",
            prevJulday=f"{prev.timetuple().tm_yday:03d}",
            curJulday=f"{curr.timetuple().tm_yday:03d}",
            
            isFirstWeekOfMonth= isFirstWeekOfMonth,
            isLastWeekOfMonth= False,
            financialYearMonth= financialYearMonth,
        )
        rows.append(row)
        curr += timedelta(days=7)
        week += 1
    
    # last date, make isLastWeekOfMonth as True
    rows[-1].isLastWeekOfMonth = True
    
    return rows
    
    
    
def get_file_utf(rows):
    lst_str = []

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
        # s.append("XXX") # Todo need to change
        
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
        # s.append(str(row.month))
        s.append(f"{row.month:02d}")
        s.append(str(row.day))
        
        
        
        lst_str.append("".join(s))
    return lst_str

def _build_bytes_for_year(year: int) -> bytes:
    rows = row_data_for_file(year)
    lst_str = get_file_utf(rows)
    
    # lines = _build_lines_for_year(year)
    return ("\n".join(lst_str) + "\n").encode("utf-8")

def generate_file(year, path=""):
    rows = row_data_for_file(year)
    lst_str = get_file_utf(rows)
    
    out_path = Path("financial_year_output.txt")
    out_path.write_text("\n".join(lst_str) + "\n", encoding="utf-8")
    print(f"Saved {len(lst_str)} lines to {out_path.resolve()}")