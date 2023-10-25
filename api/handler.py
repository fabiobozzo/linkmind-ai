from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

from model.reader import ModelReader
from scrape.scraper import retrieve_content


class Settings(BaseSettings):
    categories_filepath: str = "Awesome API"
    root_path: str
    model_config = SettingsConfigDict(env_file=".env")


class Request(BaseModel):
    url: str


class Response(BaseModel):
    label: str
    name: str
    description: str = ''


app = FastAPI(title="Linkmind AI")


def load_settings() -> Settings:
    return Settings()


def load_model(settings: Settings = Depends(load_settings)) -> ModelReader:
    return ModelReader(settings.categories_filepath, settings.root_path)


@app.post("/classify", response_model=Response)
def classify(req: Request, model_reader: ModelReader = Depends(load_model)):
    content = retrieve_content(req.url, "body")
    if content is None:
        raise HTTPException(status_code=400, detail="cannot retrieve content from url")
    prediction = model_reader.classify(f"{content['title']}\n{content['content']}")
    res = Response(label=prediction['label'], name=prediction['name'])
    if 'description' in prediction:
        res.description = prediction['description']
    return res
    # return {'label': 'xxx', 'name': content['title']}
