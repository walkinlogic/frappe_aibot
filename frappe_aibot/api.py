import frappe
import re

from langchain.llms import OpenAI
from langchain.memory import RedisChatMessageHistory, ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate
import datetime


# Note: Copied the default template and added extra instructions for code output
prompt_template = PromptTemplate(
	input_variables=["history", "input"],
	output_parser=None,
	partial_variables={},
	template="""
	The following is a friendly conversation between a human and an AI. The AI is talkative and provides lots of specific details from its context. If the AI does not know the answer to a question, it truthfully says it does not know.
	
	
	Current conversation:
	{history}
	Human: {input}
	AI:""",
	template_format="f-string",
	validate_template=True,
)
def is_valid_select_query(query):
    # Check if the query starts with SELECT
    select_pattern = r'^\s*select\b'
    if not re.match(select_pattern, query, re.IGNORECASE):
        return False  # Not a SELECT query
    
    # Check for the presence of DELETE, UPDATE, or ALTER keywords
    forbidden_keywords = ['delete', 'update', 'alter']
    for keyword in forbidden_keywords:
        pattern = rf'\b{keyword}\b'
        if re.search(pattern, query, re.IGNORECASE):
            return False  # Contains forbidden keywords
    
    return True  # It's a valid SELECT query without forbidden keywords

@frappe.whitelist()
def get_chatbot_history(**kwargs):
	# Chat History 
	session_id = frappe.session.user
	if kwargs.get("session_id"):
		session_id = str(kwargs["session_id"])
	doctypename = ""
	if kwargs.get("doctype"):
		doctypename = " AND doctype_name = '%s'"%str(kwargs["doctype"])
	sqlquery = """SELECT 
					m.human,
					m.ai,
					m.user_name, 
					m.doctype_name,
					m.added_date
				FROM "tabChat History" m   
				WHERE m.name IS NOT NULL 
				AND m.user_name = '%s' 
				%s
				ORDER BY m.idx DESC 
					"""%(session_id, doctypename)
		
	historydata = frappe.db.sql(sqlquery, as_dict=1)	
	
	message_history = RedisChatMessageHistory(
		session_id=session_id,
		url=frappe.conf.get("redis_cache") or "redis://localhost:6379/0",
	)
	doctypename = ""
	message_history.clear()
	if kwargs.get("doctype"):
		doctypename = " AND parent = '%s'"%str(kwargs["doctype"])
		sqlquery = """SELECT 
						fieldname,
						label,
						fieldtype
					FROM "tabDocField" m   
					WHERE m.name IS NOT NULL  %s AND fieldtype NOT IN ('Tab Break', 'Section Break', 'Heading', 'Column Break', 'Table', 'HTML', 'Table MultiSelect')
					ORDER BY m.idx DESC; 
						"""%(doctypename)
			
		data = frappe.db.sql(sqlquery, as_dict=1)

		fields = []
		for d in data:
			# fields.append(f'{d.fieldname}  as "{d.label}" -- "{frappe.db.type_map.get(d.fieldtype)[0]}"')
			fields.append(f'{d.fieldname}  as "{d.label}"')

		field = ",".join(str(x) for x in fields)
		doctype_name = "%s"%str(kwargs["doctype"])
		sqlquery = """SELECT 
						%s
					FROM "tab%s" m   
					WHERE m.name IS NOT NULL 
					ORDER BY m.idx DESC
					LIMIT 10; 
						"""%(field,doctype_name)
		data = frappe.db.sql(sqlquery, as_dict=1)
		# message_history.add_ai_message(sqlquery)
		message_history.add_ai_message(str(frappe.as_json(data)))
	else:
		sqlquery = """SELECT 
						name
					FROM "tabDocType" m   
					WHERE m.name IS NOT NULL
					ORDER BY m.idx DESC; 
						"""
			
		docdata = frappe.db.sql(sqlquery, as_dict=1)

		queries=[]
		for d in docdata:
			doctypename = " AND parent = '%s'"%str(d["name"])
			sqlquery = """SELECT 
							fieldname,
							label,
							fieldtype
						FROM "tabDocField" m   
						WHERE m.name IS NOT NULL  %s AND fieldtype NOT IN ('Tab Break', 'Section Break', 'Heading', 'Column Break', 'Table', 'HTML', 'Table MultiSelect')
						ORDER BY m.idx DESC; 
							"""%(doctypename)
				
			data = frappe.db.sql(sqlquery, as_dict=1)

			fields = []
			for dc in data:
				# fields.append(f'{d.fieldname}  as "{d.label}" -- "{frappe.db.type_map.get(d.fieldtype)[0]}"')
				fields.append(f'{dc.fieldname}  as "{dc.label}"')

			field = ",".join(str(x) for x in fields)
			doctype_name = "%s"%str(d["name"])
			queries.append(f"""SELECT 
							%s
						FROM "tab%s" m   
						WHERE m.name IS NOT NULL 
						ORDER BY m.idx DESC; 
							"""%(field,doctype_name))
			queries.append(f""" -- table name "tab%s"  table name  case-sensitive table name enclosed in double qoutes;"""%(str(d["name"]))) 				 

		sqlqueries = " ".join(str(x) for x in queries)
		message_history.add_ai_message(sqlqueries)
	return historydata


@frappe.whitelist()
def get_chatbot_response(**kwargs) -> str:
	session_id = frappe.session.user
	if kwargs.get("session_id"):
		session_id = str(kwargs["session_id"])

	if kwargs.get("prompt_message"):
		prompt_message = "%s"%(str(kwargs["prompt_message"]))

	# if kwargs.get("doctype"):
	# 	prompt_message += ' table name "tab%s"  table name  case-sensitive table name enclosed in double qoutes '%(str(kwargs["doctype"])) 
	opeai_api_key = get_key_from_settings()
	openai_model = get_model_from_settings()

	if not opeai_api_key:
		frappe.throw("Please set `openai_api_key` in AIBot Settings")

	llm = OpenAI(model_name=openai_model, temperature=0, openai_api_key=opeai_api_key)
	message_history = RedisChatMessageHistory(
		session_id=session_id,
		url=frappe.conf.get("redis_cache") or "redis://localhost:6379/0",
	)

	

	memory = ConversationBufferMemory(memory_key="history", chat_memory=message_history)
	conversation_chain = ConversationChain(llm=llm, memory=memory, prompt=prompt_template)

	response = conversation_chain.run(prompt_message)
	pattern= r'```sql\s([\s\S]*?)\s```'
	airespons = re.findall(pattern, response)
	if airespons:
		if is_valid_select_query(airespons[0]):
			airesponse = f"<div style='padding:10px; margin:10px; border:1px solid black; background-color:#f0f0f0;'>{airespons[0]}</div>"
		else:
			airesponse = "SQL contains forbidden keywords or is not a valid SELECT query."	
	else:
		airesponse = response
	# if response.count("```") >= 2:  # Ensure there are at least 2 occurrences to replace
	# 	parts = response.split("```", 2)  # Split at the first two sets of triple apostrophes
	# 	response = f"<div style='padding:10px; margin:10px; border:1px solid black; background-color:#f0f0f0;'>{parts[1]}</div>"
	# else:
	# 	# If no triple apostrophes, return the original response
	# 	response = response

	if kwargs.get("prompt_message"):
		prompt_message = "%s"%(str(kwargs["prompt_message"]))	
	my_route_card = frappe.new_doc("Chat History")
	my_route_card.added_date = datetime.datetime.now()
	my_route_card.human = prompt_message
	my_route_card.ai = airesponse 
	my_route_card.user_name = session_id 
	doctype_name = ''
	if kwargs.get("doctype"):
		doctype_name = str(kwargs["doctype"])
	
	my_route_card.doctype_name = doctype_name 
	my_route_card.save(ignore_permissions=1)

	return  airesponse 


def get_model_from_settings():
	return (
		frappe.db.get_single_value("AIBot Settings", "openai_model") or "gpt-3.5-turbo"
	)

def get_key_from_settings():
	return (
		frappe.db.get_single_value("AIBot Settings", "openai_api_key") or None
	)
