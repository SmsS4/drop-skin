import datetime, pytz
import threading
import time

from src import config
import fastapi
import requests
import uvicorn

TIMEZONE = pytz.timezone(zone="Asia/Tehran")


class Account:
    def __init__(self, name: str, authorization: str):
        self.name = name
        self.headers = {
            "authorization": f"Bearer {authorization}",
            "sec-ch-ua": '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
            "sec-ch-ua-platform": "Linux",
            "sec-ch-ua-mobile": "?0",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        }

    def last(self) -> tuple[datetime.datetime, bool]:
        response = requests.get(
            "https://api.drop.skin/daily-auth/last",
            headers=self.headers,
        )
        result = response.json()
        if result["canOpen"]:
            return datetime.datetime.now(), True
        return (
            datetime.datetime.strptime(
                result["data"].split(".")[0],
                "%Y-%m-%dT%H:%M:%S",
            )
            + datetime.timedelta(seconds=10),
            False,
        )

    def open(self) -> tuple[int | None, str | None]:
        response = requests.post(
            "https://api.drop.skin/daily-auth/open",
            headers=self.headers,
        )
        result = response.json()
        return result["amount"], result["case"]


class CaseOpener:
    def __init__(self, accounts: list[Account]) -> None:
        self.accounts = accounts
        self.last_open: dict[str, tuple[int | None, str | None]] = {}

    def wait_for_next_drop(self) -> None:
        next_open_time: datetime.datetime = None  # type: ignore
        for account in self.accounts:
            next_open_time_account, _ = account.last()
            if next_open_time is None:
                next_open_time = next_open_time_account
            next_open_time = min(next_open_time, next_open_time_account)
        print(
            "wating",
            (datetime.datetime.now() - next_open_time).total_seconds(),
            "till next drop",
        )
        time.sleep((datetime.datetime.now() - next_open_time).total_seconds())

    def worker(self) -> None:
        try:
            while True:
                self.wait_for_next_drop()
                for account in self.accounts:
                    if account.last()[1]:
                        print("open daily case for", account.name)
                        drop = account.open()
                        print("drop:", drop)
                        self.last_open[account.name] = drop
                        time.sleep(1)
        except Exception as e:
            print("exception", e)
            time.sleep(15 * 60)


app = fastapi.FastAPI()
case_opener = CaseOpener(
    accounts=[
        Account(
            name=name,
            authorization=token,
        ) for name, token in config.accounts.items()
    ]
)

threading.Thread(target=case_opener.worker).start()

@app.get("/")
def get():
    result = []
    for account in case_opener.accounts:
        next_drop, _ = account.last()
        next_drop = next_drop.astimezone(TIMEZONE)
        last_drop = case_opener.last_open.get(account.name, None)
        result.append(
            {
                "name": account.name,
                "next": next_drop,
                "last drop": last_drop,
            }
        )
    return result

uvicorn.run(app=app, host="0.0.0.0", port=5000)
