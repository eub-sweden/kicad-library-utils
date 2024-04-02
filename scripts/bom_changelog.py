from openpyxl import Workbook
from openpyxl import load_workbook
from openpyxl.worksheet.worksheet import Worksheet

from dataclasses import dataclass
import argparse
import logging
import pathlib

logging.basicConfig(level=logging.DEBUG)

@dataclass
class BomColumnIndex:
    MANUFACTURER_STR = "manufacturer"
    PART_NUMBER_STR = "manufacturer part number"
    QUANTITY_STR = "quantity per pcb"
    REFERENCES_STR = "references"

    manufacturer: int = None
    part_number: int = None
    quantity: int = None
    references: int = None


@dataclass
class BomRow:
    manufacturer: str
    part_number: str
    quantity: int
    references: list[str]


def extract_column_indexes(sheet: Worksheet, header_row=1) -> BomColumnIndex:
    column_indexes = BomColumnIndex()

    for idx, col in enumerate(sheet.iter_cols(min_row=header_row, max_row=header_row)):
        for cell in col:
            match str(cell.value).lower():
                case BomColumnIndex.MANUFACTURER_STR:
                    column_indexes.manufacturer = idx

                case BomColumnIndex.PART_NUMBER_STR:
                    column_indexes.part_number = idx

                case BomColumnIndex.QUANTITY_STR:
                    column_indexes.quantity = idx

                case BomColumnIndex.REFERENCES_STR:
                    column_indexes.references = idx

    return column_indexes


def extract_bom_rows(sheet: Worksheet, first_data_row=2) -> [BomRow]:
    col_index = extract_column_indexes(sheet)

    bom_rows = []
    for row in sheet.iter_rows(min_row=first_data_row, values_only=True):
        bom_row = BomRow(
            manufacturer=str(row[col_index.manufacturer] or ''),
            part_number=str(row[col_index.part_number] or ''),
            quantity=int(row[col_index.quantity]),
            references=row[col_index.references].split(),
        )
        bom_rows.append(bom_row)

    return bom_rows

def find_bom_row_changes(old_bom: [BomRow], new_bom: [BomRow]) -> ([BomRow], ([BomRow], [BomRow]), [BomRow]):
    removed_rows = []
    new_rows = []
    quantity_changed_rows = []

    for new_row in new_bom:
        found = False
        for old_row in old_bom:
            if new_row.part_number != old_row.part_number:
                continue

            if new_row.manufacturer != old_row.manufacturer:
                logging.warning("Manufacturer changed, can cause buggy output?")
                continue

            if new_row.references != old_row.references:
                quantity_changed_rows.append((old_row, new_row))

            old_bom.remove(old_row)
            found = True
            break

        if not found:
            new_rows.append(new_row)

    removed_rows = old_bom

    return new_rows, quantity_changed_rows, removed_rows

def longest_strings(boms: [[BomRow]]) -> (int, int):
    longest_man = len("Manufacturer")
    longest_part = len("Part number")

    for bom in boms:
        for row in bom:
            man_len = len(row.manufacturer)
            part_len = len(row.part_number)

            longest_man = man_len if man_len > longest_man else longest_man
            longest_part = part_len if part_len > longest_part else longest_part

    return longest_man, longest_part


def diff_bom(old_path: pathlib.Path, new_path: pathlib.Path):
    old_sheet = load_workbook(old_path).active
    new_sheet = load_workbook(new_path).active

    old_bom = extract_bom_rows(old_sheet)
    new_bom = extract_bom_rows(new_sheet)

    new_rows, quantity_changed_rows, removed_rows = find_bom_row_changes(old_bom, new_bom)

    longest_man, longest_part = longest_strings([new_rows, (quantity_changed_rows[0] if len(quantity_changed_rows) else []), removed_rows])

    longest_refs = len('Reference')
    changed_rows = []
    for old_row, new_row in quantity_changed_rows:
        removed_refs = set(old_row.references).difference(set(new_row.references))
        added_refs = set(new_row.references).difference(set(old_row.references))

        change_refs = []
        if removed_refs:
            change_refs += [f"-{ref}" for ref in removed_refs]
        if added_refs:
            change_refs += [f"+{ref}" for ref in added_refs]

        change_refs_str = " ".join(change_refs)
        quantity_change = new_row.quantity - old_row.quantity
        changed_rows.append((old_row, change_refs_str, quantity_change))

        longest_refs = len(change_refs_str) if len(change_refs_str) > longest_refs else longest_refs

    print(f"| Change   | {'Manufacturer':{longest_man}} | {'Part number':{longest_part}} | Quantity | {'Reference':{longest_refs}} |")
    print(f"| -------- | {'------------':{'-'}>{longest_man}} | {'-----------':{'-'}>{longest_part}} | -------- | {'---------':{'-'}>{longest_refs}} |")
    for new_row in new_rows:
        print(f"| Add      | {new_row.manufacturer:{longest_man}} | {new_row.part_number:{longest_part}} |          | {'':{longest_refs}} |")
    for removed_row in removed_rows:
        print(f"| Remove   | {removed_row.manufacturer:{longest_man}} | {removed_row.part_number:{longest_part}} |          | {'':{longest_refs}} |")
    for changed_row, change_refs_str, quantity_change in changed_rows:
        print(f"| Quantity | {changed_row.manufacturer:{longest_man}} | {changed_row.part_number:{longest_part}} | {quantity_change:<+{len('Quantity')}} | {change_refs_str:{longest_refs}} |")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="ProgramName",
        description="What the program does",
        epilog="Text at the bottom of help",
    )
    parser.add_argument("old", type=pathlib.Path)
    parser.add_argument("new", type=pathlib.Path)

    args = parser.parse_args()

    diff_bom(args.old, args.new)
