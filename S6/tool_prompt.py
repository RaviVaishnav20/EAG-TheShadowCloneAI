
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
                # Get basic tool properties
                desc = getattr(tool, 'description', 'No description available')
                name = getattr(tool, 'name', f'tool_{i}')
                params = tool.inputSchema
                
                # Handle the case where the input is a Pydantic class
                if '$defs' in params:
                    # Extract parameter information
                    param_details = []
                    for param_name, param_info in params['properties'].items():
                        # Check if the parameter references a class definition
                        if '$ref' in param_info:
                            ref_path = param_info['$ref']
                            class_name = ref_path.split('/')[-1]
                            
                            # Get the class definition
                            if class_name in params['$defs']:
                                class_def = params['$defs'][class_name]
                                class_desc = class_def.get('description', '')
                                
                                # Format as a single complex parameter
                                class_properties = []
                                if 'properties' in class_def:
                                    for prop_name, prop_info in class_def['properties'].items():
                                        # Handle different property types
                                        if 'type' in prop_info:
                                            prop_type = prop_info['type']
                                        elif 'anyOf' in prop_info:
                                            prop_type = ' or '.join([t.get('type', 'unknown') for t in prop_info['anyOf']])
                                        else:
                                            prop_type = 'unknown'
                                        
                                        class_properties.append(f"{prop_name}: {prop_type}")
                                
                                # Create a descriptive parameter format
                                props_str = ', '.join(class_properties)
                                param_details.append(f"{param_name}: {class_name}({props_str})")
                        else:
                            # Regular parameter
                            param_type = param_info.get('type', 'object')
                            param_details.append(f"{param_name}: {param_type}")
                
                # Handle regular input schema without $defs
                elif 'properties' in params:
                    param_details = []
                    for param_name, param_info in params['properties'].items():
                        param_type = param_info.get('type', 'unknown')
                        param_details.append(f"{param_name}: {param_type}")
                else:
                    param_details = ['no parameters']
                
                params_str = ', '.join(param_details)
                tool_desc = f"{i+1}. {name}({params_str}) - {desc}"
                tools_description.append(tool_desc)
                
            except Exception as e:
                print(f"Error processing tool {i}: {e}")
                tools_description.append(f"{i+1}. Error processing tool {name}: {e}")
        
        return "\n".join(tools_description)
        
    except Exception as e:
        print(f"Error creating tools description: {e}")
        raise Exception(f"Error creating tools description: {e}")