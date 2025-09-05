# Building an MCP-Powered AI Agent with Gemini and mcp-agent Framework: A Step-by-Step Implementation Guide

By [**Asif Razzaq**](https://www.marktechpost.com/author/6flvq/) \-

August 17, 2025

In this tutorial, we walk through building an advanced AI agent using the [**mcp-agent**](https://github.com/lastmile-ai/mcp-agent) and Gemini. We start by setting up a robust environment with all the necessary dependencies and then implement an MCP tool [server](https://www.marktechpost.com/2025/08/08/proxy-servers-explained-types-use-cases-trends-in-2025-technical-deep-dive/) that provides structured services such as web search, data analysis, code execution, and weather information. By wiring these tools into an MCP client powered by Gemini, we demonstrate how context-aware reasoning can be combined with external tool execution. Throughout, we emphasize asynchronous design, tool schema definition, and seamless integration between the MCP layer and Gemini’s generative capabilities, ensuring our agent remains modular, extensible, and production-ready. Check out the [**FULL CODES here**](https://github.com/Marktechpost/AI-Tutorial-Codes-Included/blob/main/mcp_gemini_agent_tutorial_Marktechpost.ipynb).

Copy Code

import subprocess  
import sys  
import os  
from typing import Dict, List, Any, Optional, Union  
import json  
import asyncio  
from datetime import datetime  
import logging

def install\_packages():  
   """Install required packages for the tutorial"""  
   packages \= \[  
       'mcp',  
       'google-generativeai',  
       'requests',  
       'beautifulsoup4',  
       'matplotlib',  
       'numpy',  
       'websockets',  
       'pydantic'  
   \]  
    
   for package in packages:  
       try:  
           subprocess.check\_call(\[sys.executable, "-m", "pip", "install", package\])  
           print(f"✅ Successfully installed {package}")  
       except subprocess.CalledProcessError as e:  
           print(f"❌ Failed to install {package}: {e}")

install\_packages()

We begin by defining an install\_packages function that specifies all the dependencies required for our tutorial, including mcp-agent, Gemini, and supporting libraries. We then run this function to automatically install each package, ensuring our environment is fully prepared before proceeding further. Check out the [**FULL CODES here**](https://github.com/Marktechpost/AI-Tutorial-Codes-Included/blob/main/mcp_gemini_agent_tutorial_Marktechpost.ipynb).

Copy Code

import google.generativeai as genai  
import requests  
from bs  
class MCPToolServer:  
   """MCP Server that provides tools for the AI agent4 import BeautifulSoup  
import matplotlib.pyplot as plt  
import numpy as np

from mcp import ClientSession, StdioServerParameters  
from mcp.client.stdio import stdio\_client  
from mcp.types import TextContent, ImageContent, EmbeddedResource  
import mcp.types as types

logging.basicConfig(level=logging.INFO)

logger \= logging.getLogger(\_\_name\_\_)

We import all the core libraries we need, from Gemini and web scraping utilities to visualization and numerical tools. We also bring in the mcp-agent modules for protocol communication and configure logging so that we can track our agent’s execution flow in real time. Check out the [**FULL CODES here**](https://github.com/Marktechpost/AI-Tutorial-Codes-Included/blob/main/mcp_gemini_agent_tutorial_Marktechpost.ipynb).

Copy Code"""

    
   def \_\_init\_\_(self):  
       self.tools \= {  
           "web\_search": {  
               "name": "web\_search",  
               "description": "Search the web for information",  
               "inputSchema": {  
                   "type": "object",  
                   "properties": {  
                       "query": {"type": "string", "description": "Search query"}  
                   },  
                   "required": \["query"\]  
               }  
           },  
           "data\_analysis": {  
               "name": "data\_analysis",  
               "description": "Analyze data and create visualizations",  
               "inputSchema": {  
                   "type": "object",  
                   "properties": {  
                       "data\_type": {"type": "string", "description": "Type of analysis"},  
                       "parameters": {"type": "object", "description": "Analysis parameters"}  
                   },  
                   "required": \["data\_type"\]  
               }  
           },  
           "code\_execution": {  
               "name": "code\_execution",  
               "description": "Execute or generate code",  
               "inputSchema": {  
                   "type": "object",  
                   "properties": {  
                       "language": {"type": "string", "description": "Programming language"},  
                       "task": {"type": "string", "description": "Code task description"}  
                   },  
                   "required": \["language", "task"\]  
               }  
           },  
           "weather\_info": {  
               "name": "weather\_info",  
               "description": "Get weather information",  
               "inputSchema": {  
                   "type": "object",  
                   "properties": {  
                       "location": {"type": "string", "description": "Location for weather"}  
                   },  
                   "required": \["location"\]  
               }  
           }  
       }  
    
   async def list\_tools(self) \-\> List\[types.Tool\]:  
       """Return list of available tools"""  
       return \[types.Tool(\*\*tool) for tool in self.tools.values()\]  
    
   async def call\_tool(self, name: str, arguments: Dict\[str, Any\]) \-\> List\[types.TextContent\]:  
       """Execute a tool and return results"""  
       if name \== "web\_search":  
           return await self.\_web\_search(arguments.get("query", ""))  
       elif name \== "data\_analysis":  
           return await self.\_data\_analysis(arguments.get("data\_type", ""), arguments.get("parameters", {}))  
       elif name \== "code\_execution":  
           return await self.\_code\_execution(arguments.get("language", ""), arguments.get("task", ""))  
       elif name \== "weather\_info":  
           return await self.\_weather\_info(arguments.get("location", ""))  
       else:  
           return \[types.TextContent(type="text", text=f"Unknown tool: {name}")\]  
    
   async def \_web\_search(self, query: str) \-\> List\[types.TextContent\]:  
       """Perform web search"""  
       try:  
           search\_url \= f"https://www.wikipedia.org/wiki/Special:Search?search={query.replace(' ', '%20')}"  
           headers \= {'User-Agent': 'Mozilla/5.0 (compatible; MCP Agent)'}  
            
           response \= requests.get(search\_url, headers=headers, timeout=10)  
           if response.status\_code \== 200:  
               soup \= BeautifulSoup(response.content, 'html.parser')  
               paragraphs \= soup.find\_all('p')\[:3\]  
               content \= "n".join(\[p.get\_text().strip() for p in paragraphs if p.get\_text().strip()\])  
                
               result \= f"🔍 Web search results for '{query}':nn{content\[:500\]}..."  
           else:  
               result \= f"❌ Web search failed with status: {response.status\_code}"  
                
       except Exception as e:  
           result \= f"❌ Web search error: {str(e)}"  
        
       return \[types.TextContent(type="text", text=result)\]  
    
   async def \_data\_analysis(self, data\_type: str, parameters: Dict) \-\> List\[types.TextContent\]:  
       """Perform data analysis"""  
       try:  
           if "sine" in data\_type.lower() or "wave" in data\_type.lower():  
               x \= np.linspace(0, 4\*np.pi, 100)  
               y \= np.sin(x) \+ np.random.normal(0, 0.1, 100)  
               title \= "Sine Wave Analysis"  
           else:  
               x \= np.random.normal(0, 1, 100)  
               y \= np.random.normal(0, 1, 100)  
               title \= "Random Data Analysis"  
            
           plt.figure(figsize=(10, 6))  
           plt.scatter(x, y, alpha=0.6)  
           plt.title(f"📊 {title}")  
           plt.xlabel("X Values")  
           plt.ylabel("Y Values")  
           plt.grid(True, alpha=0.3)  
           plt.show()  
            
           stats \= {  
               "mean\_x": np.mean(x),  
               "mean\_y": np.mean(y),  
               "std\_x": np.std(x),  
               "std\_y": np.std(y),  
               "correlation": np.corrcoef(x, y)\[0,1\]  
           }  
            
           result \= f"📊 Data Analysis Results:n"  
           result \+= f"Dataset: {title}n"  
           result \+= f"Sample size: {len(x)}n"  
           result \+= f"X \- Mean: {stats\['mean\_x'\]:.3f}, Std: {stats\['std\_x'\]:.3f}n"  
           result \+= f"Y \- Mean: {stats\['mean\_y'\]:.3f}, Std: {stats\['std\_y'\]:.3f}n"  
           result \+= f"Correlation: {stats\['correlation'\]:.3f}n"  
           result \+= f"n📈 Visualization displayed above\!"  
            
       except Exception as e:  
           result \= f"❌ Data analysis error: {str(e)}"  
        
       return \[types.TextContent(type="text", text=result)\]  
    
   async def \_code\_execution(self, language: str, task: str) \-\> List\[types.TextContent\]:  
       """Handle code generation/execution"""  
       try:  
           if language.lower() \== "python":  
               if "fibonacci" in task.lower():  
                   code \= '''def fibonacci(n):  
   """Generate fibonacci sequence up to n terms"""  
   if n \<= 0:  
       return \[\]  
   elif n \== 1:  
       return \[0\]  
   elif n \== 2:  
       return \[0, 1\]  
    
   fib \= \[0, 1\]  
   for i in range(2, n):  
       fib.append(fib\[i-1\] \+ fib\[i-2\])  
   return fib

\# Example usage  
print("First 10 fibonacci numbers:", fibonacci(10))'''  
                    
               elif "sort" in task.lower():  
                   code \= '''def quicksort(arr):  
   """Quick sort implementation"""

def main():  
   """Main function for {task}"""  
   print("Implementing: {task}")  
   \# Add your implementation here  
   pass

if \_\_name\_\_ \== "\_\_main\_\_":  
   main()'''  
                
               result \= f"💻 Python Code for '{task}':nn\`\`\`pythonn{code}n\`\`\`"  
                
               if "fibonacci" in task.lower():  
                   try:  
                       exec(code)  
                       result \+= "nn✅ Code executed successfully\!"  
                   except Exception as exec\_error:  
                       result \+= f"nn⚠️ Execution note: {exec\_error}"  
                
           else:  
               result \= f"💻 Code template for {language}:nn"  
               result \+= f"// {task}n// Language: {language}n// Add your implementation here"  
                
       except Exception as e:  
           result \= f"❌ Code generation error: {str(e)}"  
        
       return \[types.TextContent(type="text", text=result)\]  
    
   async def \_weather\_info(self, location: str) \-\> List\[types.TextContent\]:  
       """Get weather information"""  
       weather\_data \= {  
           "temperature": np.random.randint(15, 30),  
           "condition": np.random.choice(\["Sunny", "Cloudy", "Rainy", "Partly Cloudy"\]),  
           "humidity": np.random.randint(40, 80),  
           "wind\_speed": np.random.randint(5, 25)  
       }  
        
       result \= f"🌤️ Weather for {location}:n"  
       result \+= f"Temperature: {weather\_data\['temperature'\]}°Cn"  
       result \+= f"Condition: {weather\_data\['condition'\]}n"  
       result \+= f"Humidity: {weather\_data\['humidity'\]}%n"  
       result \+= f"Wind Speed: {weather\_data\['wind\_speed'\]} km/hn"  
       result \+= f"n📝 Note: This is simulated data. For real weather, use a weather API service."  
      

       return \[types.TextContent(type="text", text=result)\]

We design the MCPToolServer class that defines and manages all the tools our agent can use, including web search, data analysis, code execution, and weather information. We implement async methods for each tool, enabling the agent to perform the requested operation, such as fetching Wikipedia text, generating visualizations, executing Python snippets, or simulating weather data, and return the results in a structured format. This structure makes our MCP server modular and easily extensible for adding more tools in the future. Check out the [**FULL CODES here**](https://github.com/Marktechpost/AI-Tutorial-Codes-Included/blob/main/mcp_gemini_agent_tutorial_Marktechpost.ipynb).

Copy Code

class MCPAgent:  
   """AI Agent using MCP (Model Context Protocol)"""  
    
   def \_\_init\_\_(self, gemini\_api\_key: Optional\[str\] \= None):  
       self.gemini\_api\_key \= gemini\_api\_key or self.\_get\_api\_key()  
       self.mcp\_server \= MCPToolServer()  
       self.conversation\_history \= \[\]  
        
       if self.gemini\_api\_key:  
           genai.configure(api\_key=self.gemini\_api\_key)  
           self.model \= genai.GenerativeModel('gemini-1.5-flash')  
           print("✅ MCP Agent initialized with Gemini\!")  
       else:  
           self.model \= None  
           print("⚠️ MCP Agent initialized without Gemini (limited functionality)")  
    
   def \_get\_api\_key(self) \-\> Optional\[str\]:  
       """Get Gemini API key"""  
       api\_key \= os.environ.get('GEMINI\_API\_KEY')  
       if not api\_key:  
           print("📝 Get your free API key from: https://makersuite.google.com/app/apikey")  
           api\_key \= input("Enter your Gemini API key (or press Enter to skip): ").strip()  
       return api\_key if api\_key else None  
    
   async def process\_request(self, user\_input: str) \-\> str:  
       """Process user request using MCP tools and Gemini"""  
       self.conversation\_history.append({"role": "user", "content": user\_input})  
        
       available\_tools \= await self.mcp\_server.list\_tools()  
       tool\_descriptions \= "n".join(\[f"- {tool.name}: {tool.description}" for tool in available\_tools\])  
        
       if self.model:  
           analysis\_prompt \= f"""  
           User request: "{user\_input}"  
            
           Available MCP tools:  
           {tool\_descriptions}  
            
           Should I use a tool for this request? If yes, specify:  
           1\. Tool name (exact match)  
           2\. Arguments as JSON  
            
           If no tool needed, respond with "NO\_TOOL".  
            
           Format: TOOL\_NAME|{{"argument": "value"}}  
           """  
            
           analysis \= self.model.generate\_content(analysis\_prompt).text.strip()  
            
           if analysis \!= "NO\_TOOL" and "|" in analysis:  
               try:  
                   tool\_name, args\_json \= analysis.split("|", 1)  
                   tool\_name \= tool\_name.strip()  
                   arguments \= json.loads(args\_json)  
                    
                   tool\_results \= await self.mcp\_server.call\_tool(tool\_name, arguments)  
                   tool\_output \= "n".join(\[content.text for content in tool\_results\])  
                    
                   final\_prompt \= f"""  
                   User asked: "{user\_input}"  
                    
                   I used the {tool\_name} tool and got this result:  
                   {tool\_output}  
                    
                   Please provide a helpful response that incorporates this information.  
                   """  
                    
                   response \= self.model.generate\_content(final\_prompt).text  
                    
               except Exception as e:  
                   response \= f"❌ Error using MCP tool: {str(e)}nnLet me help you directly instead.n"  
                   response \+= self.model.generate\_content(user\_input).text  
           else:  
               response \= self.model.generate\_content(user\_input).text  
       else:  
           response \= f"🤖 MCP Agent received: {user\_input}n"  
           response \+= "Available tools: " \+ ", ".join(\[tool.name for tool in available\_tools\])  
           response \+= "n💡 Configure Gemini API for full functionality\!"  
        
       self.conversation\_history.append({"role": "assistant", "content": response})

       return response

We define an MCPAgent that wires Gemini to our MCP tool server and maintains conversation history, enabling us to reason, decide on a tool, execute it, and synthesize the result. We fetch the Gemini API key, configure the model, and in process\_request, we prompt Gemini to choose a tool (or answer directly), run the selected tool asynchronously, and compose a final response grounded in the tool output. Check out the [**FULL CODES here**](https://github.com/Marktechpost/AI-Tutorial-Codes-Included/blob/main/mcp_gemini_agent_tutorial_Marktechpost.ipynb).

Copy Code

async def run\_mcp\_demo():  
   """Run comprehensive MCP Agent demo"""  
   print("🚀 MCP Agent Demo Starting\!")  
   print("=" \* 50)  
    
   agent \= MCPAgent()  
    
   demo\_queries \= \[  
       "Search for information about machine learning",  
       "Create a data visualization with sine wave analysis",  
       "What's the weather like in New York?",  
       "Explain how artificial intelligence works"  
   \]  
    
   print("n🧪 Running MCP Tool Demonstrations:")  
   print("-" \* 40)  
    
   for i, query in enumerate(demo\_queries, 1):  
       print(f"n📝 Query {i}: {query}")  
       print("-" \* 30)  
        
       response \= await agent.process\_request(query)  
       print(response)  
        
       if i \< len(demo\_queries):  
           print("n⏳ Next demo in 3 seconds...")  
           await asyncio.sleep(3)  
    
   print("n✅ MCP Demo completed\!")  
   return agent

async def interactive\_mcp\_mode(agent: MCPAgent):  
   """Interactive mode with MCP agent"""  
   print("n💬 Interactive MCP Mode\!")  
   print("Type 'quit' to exit, 'tools' to see available MCP tools")  
    
   while True:  
       try:  
           user\_input \= input("n🗣️ You: ").strip()  
            
           if user\_input.lower() \== 'quit':  
               print("👋 Goodbye\!")  
               break  
           elif user\_input.lower() \== 'tools':  
               tools \= await agent.mcp\_server.list\_tools()  
               print("n🛠️ Available MCP Tools:")  
               for tool in tools:  
                   print(f"  \- {tool.name}: {tool.description}")  
               continue  
           elif not user\_input:  
               continue  
            
           response \= await agent.process\_request(user\_input)  
           print(f"n🤖 MCP Agent: {response}")  
            
       except KeyboardInterrupt:  
           print("n👋 Goodbye\!")  
           break  
       except Exception as e:  
           print(f"❌ Error: {str(e)}")

if \_\_name\_\_ \== "\_\_main\_\_":  
   print("🎯 Advanced AI Agent with MCP (Model Context Protocol)")  
   print("Built for Google Colab with Gemini API integration")  
   print("=" \* 60)  
    
   agent \= asyncio.run(run\_mcp\_demo())  
    
   asyncio.run(interactive\_mcp\_mode(agent))  
    
   print("n📚 MCP Tutorial Complete\!")  
   print("n🔍 What you learned:")  
   print("✅ How to implement MCP (Model Context Protocol) tools")  
   print("✅ Tool registration and discovery")  
   print("✅ Structured tool calling with arguments")  
   print("✅ Integration between MCP tools and Gemini AI")

   print("✅ Async tool execution and response handling")

We run a scripted demo that initializes MCPAgent, executes a suite of representative queries, and prints Gemini-driven, tool-augmented responses with short pauses between runs. We then drop into an interactive loop where we can list tools, send arbitrary prompts, and observe end-to-end MCP orchestration, before printing a concise recap of the concepts covered.

In conclusion, we now have a comprehensive MCP agent that dynamically decides when to use external tools and how to merge their outputs into meaningful responses. We validate the agent across multiple queries, showcasing its ability to search, analyze, generate, and simulate real-world interactions with Gemini as the reasoning engine. By combining structured MCP protocols with the flexibility of Gemini, we create a template for building powerful AI systems that are both interactive and technically grounded.

