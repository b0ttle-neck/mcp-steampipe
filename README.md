# Steampipe MCP

This is a simple steampipe MCP server. This acts as a bridge between your AI model and Steampipe tool.

## Pre-requisites
- Python 3.10+ installed.
- uv installed (my fav) and mcp[cli]
- Steampipe installed and working.
- Steampipe plugin configured (e.g., github) with necessary credentials (e.g., token in ~/.steampipe/config/github.spc).
- Any LLM supporting MCP. I am using Claude Here.
- Node.js and npx installed (required for the MCP Inspector and potentially for running some MCP servers).


## Running MCP Interceptor
This is an awesome tool for testing your if your MCP server is working as expected
- Running the Interceptor
```npx -y @modelcontextprotocol/inspector uv --directory . run steampipe_mcp_server.py```
- A browser window should open with the MCP Inspector UI (usually at http://localhost:XXXX).
- Wait for the "Connected" status on the left panel.
- Go to the Tools tab.
- You should see the run_steampipe_query tool listed with its description.
- Click on the tool name.
- In the "Arguments" JSON input field, enter a valid Steampipe query:
```
{
  "query": "select name, fork_count from github_my_repository "
}
```
- execute and view the json results

## Running the tool
Pretty straightforward. Just run the interceptor and make sure the tool is working from the directory. Then add the server configuration to the respective LLM and select the tool from the LLM. 

## TroubleShooting

- If the tool is not found in the interceptor then that means @mcp.tool() decorator has some issue.
- Execution error - Look at the "Result" in the Inspector and the server logs (stderr) in your terminal. Did Steampipe run? Was there a SQL error? A timeout? A JSON parsing error? Adjust the Python script accordingly.
```
tail -f ~/Library/Logs/Claude/mcp.log
tail -f ~/Library/Logs/Claude/mcp-server-steampipe.log
```
**Security Risk**
Claude blindly executes your sql query in this POC so there is possibility to generate and execute arbitary SQL Queries via Steampipe using your configured credentials. 
