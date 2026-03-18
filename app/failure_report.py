
REPORTS_DIR = "/tmp/failure_report"
os.makedirs(REPORTS_DIR, exist_ok=True)

def write_report(upload_id: str, index: int, data: str, error: str):
    path = f"{REPORTS_DIR}/{upload_id}.csv"
    is_exist = os.path.exists(path)

    with open(path, "a", newline="") as failure_report:
        report_writer = csv.DictWriter(failure_report, fieldnames=["index", "data", "error"])

        #  Write the header only once when the file is first created.
        if not is_exist:
            report_writer.writeheader()

        report_writer.writerow({"index": index, "data": data, "error": error})


def generate_csv(upload_id: str):
    path = f"{REPORTS_DIR}/{upload_id}.csv"

    def output():
        with open(path, "r", newline="") as failure_report:
            for line in failure_report:
                yield line
 
    return StreamingResponse(
        output(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{upload_id}_failures.csv"'},
    )

