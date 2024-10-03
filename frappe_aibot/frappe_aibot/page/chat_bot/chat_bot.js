var bot_docs;
var msgerForm ;
var msgerInput;
var msgerChat ;
var msgerSendBtn ;
var idSession;
const USER_ID = frappe.session.user;

const BOT_IMG = "/assets/frappe_aibot/img/chatgpt.svg";
	var PERSON_IMG ;
	const BOT_NAME = "ChatGPT";
	const PERSON_NAME = "You";   


frappe.pages['chat-bot'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'AI Chat Bot',
		single_column: true
	});
	
	filters = {
		add:async function (page) {
			bot_docs = page.add_field({
				label: "Select Form",
				//fieldtype: "Select",
				fieldtype:'Link',
				fieldname: "doctype", 
				options: "DocType",
				//options: " \nSchool\nMonitoring\nSchool Monitoring Form\nEmployee", 
				change: function(){
					$('.msger-chat').html('');
					var doctype = bot_docs.value;
					getHistory(doctype)
				}
			});
		}
	}

	$(frappe.render_template("chat_bot")).appendTo(page.main);
	filters.add(page);
	msgerForm = getselecter(".msger-inputarea");
	msgerInput = getselecter(".msger-input");
	msgerChat = getselecter(".msger-chat");
	msgerSendBtn = getselecter(".msger-send-btn");
	idSession = getselecter(".id_session");


	PERSON_IMG = "https://api.dicebear.com/5.x/micah/svg?seed=" + document.getElementById("id_session").value
	
	 
	   
	 
	getHistory(null)
	msgerForm.addEventListener("submit", event => {
		event.preventDefault();
	
		const msgText = msgerInput.value;
		if (!msgText) return;
	
		appendMessage(PERSON_NAME, PERSON_IMG, "right", msgText);
		msgerInput.value = "";
		var doctype = bot_docs.value;
		sendMsg(msgText,doctype)
	});

} 
 
//   frappe.pages["chat-bot"].on_page_show = function (wrapper) {
// 	load_aibot_ui(wrapper);
//   };
  
//   function load_aibot_ui(wrapper) {
// 	let $parent = $(wrapper).find(".layout-main-section");
// 	$parent.empty();
  
// 	frappe.require("assets/frappe_aibot/js/aibot_ui.bundle.jsx").then(() => {
// 	  new AiBotUI.ui.AiBotUI({
// 		wrapper: $parent,
// 		page: wrapper.page,
// 	  });
// 	});
//   }
  