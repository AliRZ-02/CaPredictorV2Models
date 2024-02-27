from fastapi import responses
from fastapi import FastAPI


# Server Object
server = FastAPI(
    title="CaPredictorV2Models",
    description="Model API for CaPredictorV2",
    version="1.0.0",
    license_info={
        "name": "MIT License",
        "url": "https://github.com/AliRZ-02/CaPredictorV2Models/blob/main/LICENSE"
    },
    redoc_url="/",
    docs_url=None
)


@server.get("/{position}", status_code=200)
def position_model(position: str):
    if position not in ["centers", "defencemen", "goalies", "wings"]:
        raise HTTPException(status_code=404, detail=f"Error in finding model for position {position}")
    
    return responses.FileResponse(f"models/model_linreg_{position}.joblib")
