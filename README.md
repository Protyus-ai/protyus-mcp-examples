# Protyus MCP server and API examples

[Protyus](https://protyus.ai) reads a STEP file and tells you how the part will be made: the DFM findings and the change that fixes each, the setups, the cycle time, what it should cost and a quote. This repository shows how to connect an AI agent to it through the Protyus MCP server, and how to call the same operations from code through the REST API.

- MCP server: `https://app.protyus.ai/api/v1/mcp` (streamable HTTP)
- REST API: described by the [OpenAPI document](https://app.protyus.ai/api/v1/openapi.json)
- More: [protyus.ai/mcp](https://protyus.ai/mcp)

## What you need

- A Protyus account on a plan with API access ([pricing](https://protyus.ai/pricing)).
- An API key from the app, under **Preferences > API keys**. It starts `ak_`.
- Your organization's id, which starts `org_`. The `get_me` tool tells you which organizations you belong to.

Keep the key out of files you commit. The examples below read it from the environment.

```sh
export PROTYUS_API_KEY=ak_...
export PROTYUS_ORG=org_...
```

## Connect an agent

### Claude Code

```sh
claude mcp add --transport http protyus https://app.protyus.ai/api/v1/mcp \
  --header "Authorization: Bearer $PROTYUS_API_KEY" \
  --header "X-Protyus-Org: $PROTYUS_ORG"
```

### Cursor

Copy [`mcp.json`](mcp.json) to `.cursor/mcp.json` in your project, or to `~/.cursor/mcp.json` for every project. It reads `PROTYUS_API_KEY` and `PROTYUS_ORG` from your environment.

### VS Code (GitHub Copilot)

Copy [`.vscode/mcp.json`](.vscode/mcp.json) into your project. VS Code asks for the key the first time and keeps it in its secret storage.

### Any other MCP client

Point it at `https://app.protyus.ai/api/v1/mcp` over streamable HTTP, with two headers:

| Header | Value |
|---|---|
| `Authorization` | `Bearer ak_...` |
| `X-Protyus-Org` | `org_...` |

## Things to ask

Once it's connected, ask your agent in plain words:

- "Analyze `bracket.step` for CNC machining in 6061 aluminum, 50 off. What will a machinist push back on?"
- "How many setups does it take on a 3-axis machine, and how many on a 5-axis?"
- "Show me the worst finding on the part."
- "I've changed the file. What did the new version fix, and what did it break?"
- "Price it at 200 off and make a quote."

The agent acts as you, with your permissions in your organization. Tools that change data say so, and a well-behaved client asks you before it calls them.

## Call the API from code

[`python/analyze.py`](python/analyze.py) uploads a STEP file, runs an analysis and prints the verdict and the findings. It uses only the Python standard library.

```sh
python python/analyze.py path/to/part.step
```

## Support

support@protyus.ai

## License

The examples are MIT licensed: see [LICENSE](LICENSE). Protyus itself is a commercial service with its own [terms](https://protyus.ai/terms).
