import pandas as pd
import openpyxl


def total_sales(
    file_path,
    sheet_name,
    translation_sheet="Language Translation.xlsx",
    output_translations=False,
    add_to=False,
    worksheet_to_add="Monthly Sales Calculation",
    create_new_spreadsheet=True,
    new_filename="Result.xlsx",
    new_worksheet="Sheet1",
):
    """
    Calculate total sales from the inputted spreadsheet
    """
    # Function to calculate hourly and postpaid sales
    def hourly_and_postpaid_sales(sales_df):
        """
        Calculate hourly and postpaid sales
        """
        # Filter out hourly and postpaid sales by getting all non-monthly sales
        hourly_and_postpaid_df = sales_df[sales_df[billing_method] != monthly]

        # Get the first row in which a particular id appears (Used to get key details and the Order Start Time)
        first_row = hourly_and_postpaid_df.groupby(resource_id).first().reset_index()

        # Get last row in which the Resource ID appears, used to get overall Order End Time
        last_row = hourly_and_postpaid_df.groupby(resource_id).last().reset_index()

        # Merge first row data with last row data (Resource ID, Order Type, Order Start Time, Order End Time columns only)
        merged_df = pd.merge(
            first_row,
            last_row[[resource_id, order_type, order_start_time, order_end_time]],
            on="Resource ID",
            how="left",
            suffixes=("_first_row", "_last_row"),
        )

        # Update Order End Time
        order_end_overall = order_end_time + "_first_row"
        last_row_start = order_start_time + "_last_row"
        last_row_end = order_end_time + "_last_row"
        last_row_order_type = order_type + "_last_row"

        # If last row is a cancellation, use the last row's Order Start Time (Order Start Time_last) as the overall Order End Time
        # Else use the last row's Order End Time (Order End Time_last) as the overall Order End Time
        merged_df[order_end_overall] = merged_df.apply(
            lambda row: row[last_row_start]
            if row[last_row_order_type] == delete_refund
            else row[last_row_end],
            axis=1,
        )

        # Drop added columns from the merge
        merged_df = merged_df.drop(
            [last_row_order_type, last_row_start, last_row_end], axis=1
        )

        # Rename columns for Start and End Time back to normal
        merged_df = merged_df.rename(
            columns={
                order_start_time + "_first_row": order_start_time,
                order_end_overall: order_end_time,
            }
        )

        # Calculate duration in hours rounded off to 2 decimal places.
        # Convert string columns to datetime
        merged_df[order_start_time] = pd.to_datetime(merged_df[order_start_time], format='%Y-%m-%d %H:%M:%S')
        merged_df[order_end_time] = pd.to_datetime(merged_df[order_end_time], format='%Y-%m-%d %H:%M:%S')

        # Calculate the duration in hours
        merged_df['Duration (Hours)'] = (merged_df[order_end_time] - merged_df[order_start_time]).astype('timedelta64[s]') / 3600

        # Convert 'Duration (Hours)' to numeric
        merged_df['Duration (Hours)'] = pd.to_numeric(merged_df['Duration (Hours)'], errors='coerce')

        # Round off the result to 2 decimal places
        merged_df['Duration (Hours)'] = merged_df['Duration (Hours)'].round(2)

        # Get usage amount by summing up the hourly charges for each Resource ID
        usage_amount = (
            hourly_and_postpaid_df.groupby(resource_id)[usage_total].sum().reset_index()
        )

        # Merge total usage amount dataframe
        final_df = pd.merge(
            merged_df,
            usage_amount,
            on=resource_id,
            how="left",
            suffixes=("_hourly", "_total"),
        )

        # Rename columns back to normal
        final_df = final_df.rename(columns={usage_total + "_total": usage_total})

        # Drop hourly usage column (there is already a column for unit price)
        final_df = final_df.drop([usage_total + "_hourly"], axis=1)

        # Get average Unit Price by dividing Usage Amount by duration
        final_df[unit_price] = (
            final_df[usage_total] / final_df["Duration (Hours)"]
        ).round(2)

        return final_df
    
    # Get translations for spreadsheet
    translations = parse_translations(translation_sheet)

    # Variables needed for calculations
    headers = translations["Header"]
    billing_method = headers["计费类型"]
    resource_id = headers["资源ID"]
    order_type = headers["订单类型"]
    order_start_time = headers["订单起始时间"]
    order_end_time = headers["订单结束时间"]
    usage_total = headers["消费原价"]
    unit_price = headers["订单原价"]
    delete_refund = translations["订单类型"]["删除退费"]
    monthly = translations["计费类型"]["按月"]

    sales_df = translate_spreadsheet_data(
        file_path, sheet_name, translations, output_translations
    )

    # Calculate hourly and postpaid sales
    output = hourly_and_postpaid_sales(sales_df)

    # Reorganize columns and exclude columns not required for our final output
    output = output[
        [
            headers["项目"],  # Project ID
            resource_id,
            headers["标识"],  # Resource Name
            headers["资源类型"],  # Resource Type
            headers["数据中心"],  # Region
            billing_method,
            headers["配置"],  # Configuration
            order_start_time,
            order_end_time,
            "Duration (Hours)",
            unit_price,
            usage_total,
        ]
    ]

    if add_to:
        with pd.ExcelWriter(file_path, engine="openpyxl", mode="a") as writer:
            # Write the DataFrame to a new worksheet
            output.to_excel(writer, sheet_name=worksheet_to_add, index=False)
    
    if create_new_spreadsheet:
        with pd.ExcelWriter(new_filename, engine="openpyxl") as writer:
            # Write the DataFrame to a new worksheet
            output.to_excel(writer, sheet_name=new_worksheet, index=False)


def parse_translations(file_path="Language Translation.xlsx"):
    """
    Read translations spreadsheet into a dictionary.

    Each worksheet's name is a key to a dictionary where the Chinese phrases are mapped to the English translation
    """
    spreadsheet = pd.ExcelFile(file_path)

    return {
        sheet: dict(
            zip(
                spreadsheet.parse(sheet).iloc[:, 0], spreadsheet.parse(sheet).iloc[:, 1]
            )
        )
        for sheet in spreadsheet.sheet_names
    }


def translate_spreadsheet_data(
    file_path, sheet_name, translations, output_translations=False
):
    """
    Takes in a spreadsheet file and a worksheet name, then using a translation guidline, translate the values in the rows and columns.

    User can output the data into the worksheet using `output_translations`
    """
    # Open sheet to translate
    untranslated_df = pd.read_excel(file_path, sheet_name=sheet_name)

    # Get translations if guidelines are not provided
    if not translations:
        translations = parse_translations()

    # Replace column values with their english translation
    cols = list(translations.keys())
    cols.remove("Header")
    for col in cols:
        untranslated_df[col].replace(translations[col], inplace=True)

    # Rename header titles
    untranslated_df.rename(columns=translations["Header"], inplace=True)

    # If user specifies to output translations, add a new worksheet to the existing file
    if output_translations:
        with pd.ExcelWriter(file_path, engine="openpyxl", mode="a") as writer:
            untranslated_df.to_excel(
                writer, sheet_name=sheet_name + "_translated", index=False
            )

    return untranslated_df