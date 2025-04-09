
import logging
import os

from jupyter_kernel_client import KernelClient
from jupyter_nbmodel_client import (
    NbModelClient,
    get_jupyter_notebook_websocket_url,
)
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("jupyter")


NOTEBOOK_PATH = os.getenv("NOTEBOOK_PATH", "notebook.ipynb")

SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8888")

TOKEN = os.getenv("TOKEN", "MY_TOKEN")


logger = logging.getLogger(__name__)


kernel = KernelClient(server_url=SERVER_URL, token=TOKEN)
kernel.start()

@mcp.tool()
async def download_earth_data_granules(
    folder_name: str, short_name: str, count: int, temporal: tuple, bounding_box: tuple
) -> str:
    """Add a code cell in a Jupyter notebook to download Earth data granules from NASA Earth Data.

    Args:
        folder_name: Local folder name to save the data.
        short_name: Short name of the Earth dataset to download.
        count: Number of data granules to download.
        temporal: (Optional) Temporal range in the format (date_from, date_to).
        bounding_box: (Optional) Bounding box in the format (lower_left_lon, lower_left_lat,
        upper_right_lon, upper_right_lat).

    Returns:
        str: Cell output
    """
    logger.info("Downloading Earth data granules")

    search_params = {"short_name": short_name, "count": count, "cloud_hosted": True}

    if temporal and len(temporal) == 2:
        search_params["temporal"] = temporal
    if bounding_box and len(bounding_box) == 4:
        search_params["bounding_box"] = bounding_box

    cell_content = f"""import earthaccess
earthaccess.login()

search_params = {search_params}  # Pass dictionary as a variable
results = earthaccess.search_data(**search_params)
files = earthaccess.download(results, "./{folder_name}")"""

    notebook = NbModelClient(
        get_jupyter_notebook_websocket_url(server_url=SERVER_URL, token=TOKEN, path=NOTEBOOK_PATH)
    )
    await notebook.start()

    cell_index = notebook.add_code_cell(cell_content)
    notebook.execute_cell(cell_index, kernel)

    await notebook.stop()

    return f"Data downloaded in folder {folder_name}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
