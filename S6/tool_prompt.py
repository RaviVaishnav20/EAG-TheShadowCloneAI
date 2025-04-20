
# def get_tools_prompt(tools):
#     try:
#         # First, let's inspect what a tool object looks like
#         # if tools:
#         #     print(f"First tool properties: {dir(tools[0])}")
#         #     print(f"First tool example: {tools[0]}")
        
#         tools_description = []
#         for i, tool in enumerate(tools):
#             try:
#                 # Get tool properties
#                 params = tool.inputSchema
#                 desc = getattr(tool, 'description', 'No description available')
#                 name = getattr(tool, 'name', f'tool_{i}')
                
#                 # Format the input schema in a more readable way
#                 if 'properties' in params:
#                     param_details = []
#                     for param_name, param_info in params['properties'].items():
#                         param_type = param_info.get('type', 'unknown')
#                         param_details.append(f"{param_name}: {param_type}")
#                     params_str = ', '.join(param_details)
#                 else:
#                     params_str = 'no parameters'

#                 tool_desc = f"{i+1}. {name}({params_str}) - {desc}"
#                 tools_description.append(tool_desc)
#                 # print(f"Added description for tool: {tool_desc}")
#             except Exception as e:
#                 print(f"Error processing tool {i}: {e}")
#                 tools_description.append(f"{i+1}. Error processing tool")
        
#         tools_description = "\n".join(tools_description)
#         return tools_description
#         # print("Successfully created tools description")
#     except Exception as e:
#         # print(f"Error creating tools description: {e}")
#         tools_description = "Error loading tools"
#         raise f"Error creating tools description: {e}"

def get_tools_prompt(tools):
    try:
        tools_description = []
        for i, tool in enumerate(tools):
            try:
                # Get tool properties
                params = tool.inputSchema
                desc = getattr(tool, 'description', 'No description available')
                name = getattr(tool, 'name', f'tool_{i}')
                
                # For Pydantic models, we need to extract the actual parameter information
                # from the referenced model schemas
                if '$ref' in params:
                    # Extract the model name from the reference
                    model_ref = params['$ref'].split('/')[-1]
                    # Look up the model in definitions
                    if 'definitions' in tool.schema and model_ref in tool.schema['definitions']:
                        model_schema = tool.schema['definitions'][model_ref]
                        if 'properties' in model_schema:
                            param_details = []
                            for param_name, param_info in model_schema['properties'].items():
                                param_type = param_info.get('type', 'unknown')
                                param_details.append(f"{param_name}: {param_type}")
                            params_str = ', '.join(param_details)
                        else:
                            params_str = 'no parameters'
                    else:
                        params_str = 'input_data: structured'
                elif 'properties' in params:
                    # Original code path for non-Pydantic tools
                    param_details = []
                    for param_name, param_info in params['properties'].items():
                        param_type = param_info.get('type', 'unknown')
                        param_details.append(f"{param_name}: {param_type}")
                    params_str = ', '.join(param_details)
                else:
                    params_str = 'input_data: unknown'

                tool_desc = f"{i+1}. {name}({params_str}) - {desc}"
                tools_description.append(tool_desc)
            except Exception as e:
                print(f"Error processing tool {i}: {e}")
                tools_description.append(f"{i+1}. Error processing tool")
        
        tools_description = "\n".join(tools_description)
        return tools_description
    except Exception as e:
        tools_description = "Error loading tools"
        raise Exception(f"Error creating tools description: {e}")    