frappe.ui.keys.add_shortcut({
    shortcut: "shift+ctrl+d",
    action: function () {
      // navigate to ask doppio bot page
      frappe.set_route("chat-bot");
    },
    description: __("Ask OPenAIBot"),
  });

 // Icons made by Freepik from www.flaticon.com




function getHistory(doctype) { 
    frappe.call({
      method: "frappe_aibot.api.get_chatbot_history",
      args:{
        user_id:USER_ID,
        doctype:doctype
      },
      freeze:true,
      callback: function (r) {
        var chatHistory = r.message;
        for (const row of chatHistory) {
            appendMessage(PERSON_NAME, PERSON_IMG, "right", row.human.replace(/(?:\r\n|\r|\n)/g, '<br>'));
            appendMessage(BOT_NAME, BOT_IMG, "left", row.ai.replace(/(?:\r\n|\r|\n)/g, '<br>'), "");
        }

      }
    }); 
}

function appendMessage(name, img, side, text, id) {
    //   Simple solution for small apps
    const msgHTML = `
    <div class="msg ${side}-msg">
      <div class="msg-img" style="background-image: url(${img})"></div>
      <div class="msg-bubble">
        <div class="msg-info">
          <div class="msg-info-name">${name}</div>
          <div class="msg-info-time">${formatDate(new Date())}</div>
        </div>

        <div class="msg-text" id=${id}>${text}</div>
      </div>
    </div>
  `;

    msgerChat.insertAdjacentHTML("beforeend", msgHTML);
    msgerChat.scrollTop += 500;
}

function sendMsg(msg,doctype) {
    msgerSendBtn.disabled = true
    var formData = new FormData();
    formData.append('msg', msg);
    formData.append('user_id', USER_ID);

    frappe.call({
      method: "frappe_aibot.api.get_chatbot_response",
      args:{
        user_id:USER_ID,
        doctype:doctype,
        prompt_message:msg
      },
      freeze:true,
      callback: function (r) {
        var chatHistory = r.message;
        appendMessage(BOT_NAME, BOT_IMG, "left", chatHistory.replace(/(?:\r\n|\r|\n)/g, '<br>'), ""); 
        msgerSendBtn.disabled = false
      }
    }); 


    // fetch('./send.php', { method: 'POST', body: formData })
    //     .then(response => response.json())
    //     .then(data => {
    //         if (data.success) {
    //             var formData = new FormData();
    //             formData.append('chat_history_id', data.id);
    //             formData.append('id', encodeURIComponent(USER_ID));
    //             fetch(`/api/method/frappe_aibot.api.get_chatbot_response?chat_history_id=${data.id}&id=${encodeURIComponent(USER_ID)}`)
    //                 .then(response => response.json())
    //                 .then(data => {
    //                     let uuid = uuidv4();
    //                     const div = document.getElementById(uuid);


    //                     if (data == "[DONE]") {
    //                         msgerSendBtn.disabled = false
    //                         eventSource.close();
    //                     } else {
    //                         let txt = data.webPages.value[0].snippet
    //                         txt += '\r\n' + data.webPages.value[0].url
    //                         if (txt !== undefined) {
    //                             appendMessage(BOT_NAME, BOT_IMG, "left", txt.replace(/(?:\r\n|\r|\n)/g, '<br>'), uuid);
    //                         }
    //                     }
    //                 });

    //         } else {
    //             let uuid = uuidv4();
    //             const div = document.getElementById(uuid);
    //             appendMessage(BOT_NAME, BOT_IMG, "left", 'Your Limit is over. Please buy subscription.', uuid);
    //         }

    //     })
    //     .catch(error => console.error(error));


}

// Utils
function getselecter(selector, root = document) {
    return root.querySelector(selector);
}

function formatDate(date) {
    const h = "0" + date.getHours();
    const m = "0" + date.getMinutes();

    return `${h.slice(-2)}:${m.slice(-2)}`;
}

function random(min, max) {
    return Math.floor(Math.random() * (max - min) + min);
}

function getCookie(cname) {
    let name = cname + "=";
    let decodedCookie = decodeURIComponent(document.cookie);
    let ca = decodedCookie.split(';');
    for (let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) == ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
        }
    }
    return "";
}

function uuidv4() {
    return ([1e7] + -1e3 + -4e3 + -8e3 + -1e11).replace(/[018]/g, c =>
        (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
    );
}

function deleteAllCookies() {
    const cookies = document.cookie.split(";");

    for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i];
        const eqPos = cookie.indexOf("=");
        const name = eqPos > -1 ? cookie.substr(0, eqPos) : cookie;
        document.cookie = name + "=;expires=Thu, 01 Jan 1970 00:00:00 GMT";
    }
}