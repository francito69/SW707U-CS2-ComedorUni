from fastapi import FastAPI, Body, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from bs4 import BeautifulSoup
import requests
import re
import uuid
from abc import ABC, abstractmethod
from typing import Dict

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions: Dict[str, dict] = {}

BASE_URL = "https://alumnos.uni.edu.pe"
HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


class Command(ABC):
    @abstractmethod
    def execute(self): pass

    @abstractmethod
    def undo(self): pass


class SetSessionCommand(Command):
    def __init__(self, cookies_list, sessions):
        self.cookies_list = cookies_list
        self.sessions = sessions
        self.sid = None

    def execute(self):
        cookies_dict = {c["name"]: c["value"] for c in self.cookies_list}
        self.sid = str(uuid.uuid4())
        self.sessions[self.sid] = {"cookies": cookies_dict}
        return self.sid

    def undo(self):
        if self.sid in self.sessions:
            del self.sessions[self.sid]


class ParseDataCommand(Command):
    def __init__(self, home_html, cursos_html):
        self.home_html = home_html
        self.cursos_html = cursos_html
        self.result = None

    def execute(self):
        soup_home = BeautifulSoup(self.home_html, "html.parser")

        nombre = soup_home.select_one(".user-name")
        codigo = soup_home.select_one(".user-code")

        soup_cursos = BeautifulSoup(self.cursos_html, "html.parser")

        creditos = 0
        label = soup_cursos.find(
            "small",
            string=re.compile(r"Cr[eé]ditos\s+[Ll]levados", re.IGNORECASE)
        )

        if label and label.parent:
            num_tag = label.parent.find("h5")
            if num_tag:
                try:
                    creditos = int(num_tag.get_text(strip=True))
                except:
                    pass

        self.result = {
            "nombre": nombre.get_text(strip=True) if nombre else "No encontrado",
            "codigo": codigo.get_text(strip=True) if codigo else "No encontrado",
            "creditos_llevados": creditos
        }

        return self.result

    def undo(self):
        self.result = None


class LogoutCommand(Command):
    def __init__(self, sid, token, sessions, base_url, headers):
        self.sid = sid
        self.token = token
        self.sessions = sessions
        self.base_url = base_url
        self.headers = headers
        self.backup = None

    def execute(self):
        if self.sid not in self.sessions:
            raise HTTPException(status_code=400, detail="Sesión no encontrada")

        self.backup = self.sessions[self.sid]["cookies"]

        payload = {"_token": self.token}
        headers_post = self.headers.copy()
        headers_post["Referer"] = f"{self.base_url}/home"

        requests.post(
            f"{self.base_url}/logout",
            data=payload,
            cookies=self.backup,
            headers=headers_post,
            timeout=10
        )

        del self.sessions[self.sid]

        return {"status": "success", "message": "Logout ejecutado"}

    def undo(self):
        if self.backup:
            self.sessions[self.sid] = {"cookies": self.backup}


@app.post("/set-session")
def set_session(data: dict = Body(...)):
    cmd = SetSessionCommand(data.get("cookies", []), sessions)
    sid = cmd.execute()
    return {"sid": sid}


@app.post("/parse-data")
def parse_data(data: dict = Body(...)):
    cmd = ParseDataCommand(
        data.get("home_html", ""),
        data.get("cursos_html", "")
    )
    return cmd.execute()


@app.post("/logout")
def logout(
    sid: str = Query(...),
    token: str = Query(...)
):
    cmd = LogoutCommand(
        sid=sid,
        token=token,
        sessions=sessions,
        base_url=BASE_URL,
        headers=HEADERS
    )
    return cmd.execute()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
