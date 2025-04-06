import subprocess
import json
import logging
import sys
from mcp.server.fastmcp import FastMCP

# Configure basic logging to stderr for debugging within Claude logs
logging.basicConfig(level=logging.INFO, stream=sys.stderr,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SteampipeMCPServer")

# Initialize FastMCP server
# The name "steampipe" will be used in the Claude config
mcp = FastMCP("steampipe")

@mcp.tool()
def run_steampipe_query(query: str) -> str:
    """
    Executes a SQL query using the Steampipe CLI and returns the results as a JSON string.

    Args:
        query: The SQL query to execute via Steampipe (e.g., "select login from github_user limit 1").
               Ensure the query is valid Steampipe SQL.
    """
    logger.info(f"Received request to run Steampipe query: {query}")
    command = ["steampipe", "query", query, "--output", "json"]

    try:
        # Execute the command
        # Set timeout to prevent hanging indefinitely (e.g., 60 seconds)
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False, # Don't raise exception on non-zero exit code, handle manually
            timeout=60
        )

        # Log stdout/stderr regardless of success for debugging
        if result.stdout:
            logger.info(f"Steampipe stdout:\n{result.stdout[:500]}...") # Log truncated stdout
        if result.stderr:
            logger.warning(f"Steampipe stderr:\n{result.stderr}")

        # Check if the command executed successfully
        if result.returncode != 0:
            error_message = f"Steampipe query failed with exit code {result.returncode}."
            if result.stderr:
                error_message += f"\nError details: {result.stderr}"
            logger.error(error_message)
            # Return the error message to Claude so it knows what went wrong
            return f"Error: {error_message}"

        # Attempt to parse the JSON output
        try:
            # Steampipe might return multiple JSON objects (one per row) or a single JSON array
            # Handle potential multiple JSON objects streamed line by line
            lines = result.stdout.strip().splitlines()
            if not lines:
                 logger.info("Steampipe returned no output.")
                 return "[]" # Return empty JSON array if no output

            # Try parsing as a single JSON array first (common case)
            try:
                parsed_json = json.loads(result.stdout)
                output_string = json.dumps(parsed_json, indent=2)
                logger.info("Successfully parsed Steampipe output as single JSON object/array.")
                return output_string
            except json.JSONDecodeError:
                 # If single parse fails, try parsing line by line
                logger.warning("Failed to parse stdout as single JSON, attempting line-by-line parsing.")
                parsed_objects = []
                for line in lines:
                    try:
                        parsed_objects.append(json.loads(line))
                    except json.JSONDecodeError as json_err_line:
                        logger.error(f"Failed to parse line: {line}. Error: {json_err_line}")
                        # Decide how to handle line parse errors, maybe return partial results or error
                if not parsed_objects:
                     logger.error("Failed to parse any lines from Steampipe output.")
                     return "Error: Failed to parse Steampipe JSON output."
                output_string = json.dumps(parsed_objects, indent=2)
                logger.info("Successfully parsed Steampipe output line-by-line.")
                return output_string

        except json.JSONDecodeError as json_err:
            error_message = f"Failed to parse Steampipe output as JSON. Error: {json_err}. Raw output: {result.stdout}"
            logger.error(error_message)
            return f"Error: {error_message}" # Return error and raw output for debugging

    except subprocess.TimeoutExpired:
        error_message = "Steampipe query timed out after 60 seconds."
        logger.error(error_message)
        return f"Error: {error_message}"
    except FileNotFoundError:
        error_message = "Steampipe command not found. Make sure it's installed and in your system PATH."
        logger.error(error_message)
        return f"Error: {error_message}"
    except Exception as e:
        error_message = f"An unexpected error occurred while running Steampipe: {e}"
        logger.exception(error_message) # Log full traceback
        return f"Error: {error_message}"

if __name__ == "__main__":
    logger.info("Starting Steampipe MCP Server...")
    # Run the server using stdio transport
    mcp.run(transport='stdio')