Switching from OpenAI to Azure OpenAI is easy and straightforward. Below are the steps you need to follow. 

 

Get Access to Azure OpenAI 

Create an Azure Account: If you don’t have an Azure account yet, you can create one for free here.  
Create an Azure OpenAI Endpoints

Identify Available Regions: Use the list of available regions for the OpenAI service and select a primary and one secondary/backup region. 
To identify the available regions for a specific model, you can refer to the Azure OpenAI Service documentation or the Azure portal.  
rkemery_0-1700602372056.png
(For a more comprehensive list of available regions for different models, you can refer to the documentation which provides information on base model regions and fine-tuning regions for various models.) 

 

Create OpenAI Service Resources: Create resources for each region selected. 

To create an Azure OpenAI resource in the Azure portal, follow these steps: 
Sign into the Azure portal with your Azure subscription. 
Select "Create a resource" and search for Azure OpenAI. Click "Create" when you find it. 
Fill in the required information on the "Basics" tab, such as subscription, resource group, region, name, and pricing tier. 
Configure network security options. 
Confirm the configuration and create the resource. 
Reference Documentation 

 

Deploy a GPT Model Using an Azure OpenAI Studio. After creating the resource, you need to deploy a model: 

Sign into Azure OpenAI Studio. 
Choose the subscription and the Azure OpenAI resource to work with. 
Under "Management," select "Deployments." 
Click "Create new deployment" and configure the fields, such as selecting a model and providing a deployment name. 
Reference Documentation 

 

Configure/Update Your Python code: 

For switching between OpenAI and Azure OpenAI Service endpoints, you need to make slight changes to your code. Update the authentication, model keyword argument, and other differences (Python examples below). 

 

Authentication 

Use environment variables for API keys and endpoints. For OpenAI, set openai.api_key and openai.organization. For Azure OpenAI, set openai.api_type, openai.api_key, openai.api_base, and openai.api_version. 

 

Here is an example of how to set up authentication for OpenAI and Azure OpenAI: 

 

 

# OpenAI 
import openai 
openai.api_key = "sk-..." 
openai.organization = "..." 
 
# Azure OpenAI 
import openai 
openai.api_type = "azure" 
openai.api_key = "..." 
openai.api_base = "https://example-endpoint.openai.azure.com" 
openai.api_version = "2023-05-15" #subject to change 
 

 

 

Keyword Argument for Model: OpenAI uses the model keyword argument, while Azure OpenAI uses deployment_id or engine interchangeably. Use the custom deployment name you chose for your model during deployment. 

 

Here is an example of how to use the keyword argument for model: 

 

# OpenAI 
completion = openai.Completion.create(prompt="<prompt>", model="text-davinci-003") 
 
# Azure OpenAI 
completion = openai.Completion.create(prompt="<prompt>", deployment_id="text-davinci-003") 
 

 

 

rkemery_2-1700602372058.png

 

 Azure OpenAI Embeddings Multiple Input Support: OpenAI currently allows a larger number of array inputs with text-embedding-ada-002. Azure OpenAI currently supports input arrays up to 16 for text-embedding-ada-002 Version 2.  

 

Reference Documentation 

Azure OpenAI Samples on GitHub

 

Handle Connectivity Errors: If a single connectivity issue occurs, retry the request. If errors persist, redirect traffic to a backup resource in the region you have created. 

 

Monitor the Azure OpenAI Usage: You can monitor the Azure OpenAI resource for their availability, performance, and operation using Azure Monitor. 

 

The dashboards are grouped into four categories: HTTP Requests, Tokens-Based Usage, PTU Utilization, and Fine-tuning 

These are the sample dashboards that you can view on the Azure monitor for Azure OpenAI services. 

rkemery_3-1700602372060.png

 

Benefits of using Azure OpenAI Service 

The Azure OpenAI Service offers several benefits concerning data, privacy, and security. 

 

Data Privacy and Exclusivity 

Your data, including prompts, outputs, embeddings, and training data, are not accessible to other customers or OpenAI.  
The data is not used to enhance OpenAI models or any Microsoft or third-party products and services.  
Fine-tuned models created within Azure OpenAI are exclusively available for your use.  
Data Processing and Storage 

The service processes a variety of data, including prompts, generated content, augmented data, and training/validation data.  
Your data remains in your designated data source; no data is copied into Azure OpenAI.  
For fine-tuning, customers can upload their training data, which is stored securely and can be double encrypted.  
Content Control and Abuse Prevention 

Azure OpenAI includes content filtering and abuse monitoring features.  
All prompts and generated content are stored securely for up to 30 days for abuse monitoring, with the option for customers to opt out.  
Microsoft personnel analyze content for harmful material and patterns that violate the code of conduct, with strict access controls.  
Customization and Fine-Tuning 

Customers can fine-tune models using their own training data.  
Fine-tuned models are stored within the same region as the Azure OpenAI resource.  
Customers have full control over their data and models, including the ability to delete them.  
Exemption from Abuse Monitoring and Human Review 

Customers can apply for an exemption from abuse monitoring and human review for sensitive or confidential data processing.  
Approved exemptions mean no prompts or completions are stored, eliminating the possibility of human review.  
Verification of Data Storage Settings 

Customers can verify the status of data storage for abuse monitoring through the Azure portal or Azure CLI.  
The article provides detailed instructions for checking the logging status.  
This service provides a secure and private environment for customers to use AI models while maintaining control over their data and adhering to strict security and privacy protocols. 
Refer here for more additional details of Data, privacy, and security for Azure OpenAI Service 

link: https://techcommunity.microsoft.com/blog/startupsatmicrosoftblog/migrating-from-openai-to-azure-openai/3989463
