from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
import asyncio
from pdb import set_trace



async def main():
    #create server parameters for studio connection
    server_params = StdioServerParameters(
        command="python",
        args=[r"C:\Users\raviv\Documents\New folder\EAG-TheShadowCloneAI\S4\src\mcp_server.py"]
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("Connected to server")

            #get available tools
            print("Requesting tool list...")
            tools_result = await session.list_tools()
            # print("Tools Result")
            # print(tools_result)
            tools = tools_result.tools
            print("Tools")
            print(len(tools))
            print(type(tools))
            # print("Tools Dir")
            tools_desc = await build_system_prompt(tools)
            print(tools_desc)
            # print(dir(tools[0]))
            # print("Tools input schema")
            # print(tools[0].inputSchema)
            # print("Tools input schema last")
            # print(tools[-1].inputSchema)
            # #get input from user
            # input_text = input("Enter your name: ")

            # #call the greeting tool
            # result = await session.call_tool(
            #     "test",
            #     arguments={"text": input_text}
            # )

            # #print the result - accessing an object properties
            # grettings = result.content[0].text

            # print(grettings)
async def build_system_prompt(tools: list) -> str:
    try:
        if tools:
            tools_description = []
            for i, tool in enumerate(tools):
                try:
                    params = tool.inputSchema
                    desc = getattr(tool, "description", "No description available")
                    name = getattr(tool, "name", f"tool_{i}")

                    #format the input schema into more readable way
                    if 'properties' in params:
                        param_details = []
                        for param_name, param_info in params['properties'].items():
                            param_type = param_info.get('type','unknown')
                            param_details.append(f"{param_name}: {param_type}")
                        param_str = ', '.join(param_details)
                    else:
                        param_str = "no parameters"
                    tool_desc = f"{i+1}. {name}({param_str}) - {desc}"
                    tools_description.append(tool_desc)
                except Exception as e:
                    print(f"Error processing tool: {i} with error: {e}")
                    tools_description.append(f"{i+1}. Error processing tool")
            return tools_description
    
    except Exception as e:
        print(f"Error creating tools descrition {e}")
        tools_description = "Error Loading tools"
        return tools_description


            
if __name__ == "__main__":
    asyncio.run(main())