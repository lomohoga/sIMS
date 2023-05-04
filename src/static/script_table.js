const timeConv = {
    "days": 1,
    "weeks": 7,
    "months": 30,
    "years": 365,
    "N/A": -1
};

const itemColumns = ["ItemID", "ItemName", "ItemDescription", "ShelfLife", "Price", "AvailableStock", "Unit"];
const requestColumns = ["RequestID", "RequestedBy", "RequestDate", "Status", "ItemID", "ItemName", "ItemDescription", "RequestQuantity", "AvailableStock", "Unit"];
const deliveryColumns = ["DeliveryID", "ItemID", "ItemName", "ItemDescription", "DeliveryQuantity", "Unit", "ShelfLife", "DeliveryDate", "ReceivedBy", "IsExpired"];

function escapeKeyword (k) {
    return k.replaceAll(/[\u2018\u2019\u201c\u201d]/gu, x => (x === '\u2018' || x === '\u2019') ? '"' : "'").replaceAll(/[:/?#\[\]@!$&'()*+,;=%]/g, x => "%" + x.charCodeAt(0).toString(16).toUpperCase());
}

async function getUsers (keyword = "") {
    return fetch(encodeURI(`/users/search${keyword === "" ? "" : "?keywords=" + escapeKeyword(keyword)}`)).then(d => d.json()).then(j => j["users"]);
}

async function populateUsers(tbody, keyword = "", type = "users") {
    while (tbody.childElementCount > 2) tbody.removeChild(tbody.lastChild);

    tbody.querySelector(".table-loading").classList.remove("hide");
    tbody.querySelector(".table-empty").classList.add("hide");

    let users = await getUsers(keyword);

    for (let x of users) {
        if(x[4] === "Admin"){
            continue;
        }
        
        let tr = document.createElement("div");
        tr.classList.add("table-row");
        tr.classList.add("delete-user-table");

        for (let i = 0; i < 5; i++) {
            let y = x[i];
            let td = document.createElement("div");
            if(y === "NULL"){
                td.innerHTML = "-"
            }
            else if(y){
                td.innerHTML = y
            }
            else{
                td.innerHTML = "-"
            }
            tr.appendChild(td);
        }

        if(type === 'users'){
            let a = document.createElement("button");
            if(x[4] === "Personnel"){
                a.innerHTML = "Promote";
                a.addEventListener("click", () => {
                    fetch("/users/promote", {
                        "method": "POST",
                        "headers": {
                            "Content-Type": "application/json"
                        },
                        "body": JSON.stringify({ "values": [x[0], x[3]] })
                    }).then(d => {
                        if (d.status === 200) window.location = "/users";
                    });
                });
            }
            else{
                a.innerHTML = "Demote";
                a.addEventListener("click", () => {
                    fetch("/users/demote", {
                        "method": "POST",
                        "headers": {
                            "Content-Type": "application/json"
                        },
                        "body": JSON.stringify({ "values": [x[0], x[3]] })
                    }).then(d => {
                        if (d.status === 200) window.location = "/users";
                    });
                });
            }

            tr.appendChild(a);
        }

        if (type === 'delete') {
            let e = document.createElement("div");
            let c = document.createElement("input");
            c.type = "checkbox";
            e.appendChild(c);
            tr.insertBefore(e, tr.firstChild);
        } else if (type === 'user-search') {
            let e = document.createElement("div");
            let b = document.createElement("button");
            b.type = "button";
            b.role = "button";
            b.innerHTML = "<i class='bi bi-plus-circle'></i><i class='bi bi-plus-circle-fill'></i>";
            b.classList.add("select-row");
            e.appendChild(b);
            tr.appendChild(e);
        }

        tbody.appendChild(tr);
    }

    tbody.querySelector(".table-loading").classList.add("hide");
    if (users.length > 0) tbody.querySelector(".table-empty").classList.add("hide");
    else tbody.querySelector(".table-empty").classList.remove("hide");

    document.dispatchEvent(new CustomEvent("tablerefresh"));
}

async function getItems (keyword = "") {
    return fetch(encodeURI(`/inventory/search${keyword === "" ? "" : "?keywords=" + escapeKeyword(keyword)}`)).then(d => d.json()).then(j => j["items"]);
}

async function populateItems (tbody, keyword = "", { stock = true, buttons = false, requesting = false } = {}) {
    while (tbody.childElementCount > 2) tbody.removeChild(tbody.lastChild);

    tbody.querySelector(".table-loading").classList.remove("hide");
    tbody.querySelector(".table-empty").classList.add("hide");

    let items = await getItems(keyword);
    let rows = [];

    for (let x of items) {
        let tr = document.createElement("div");
        tr.classList.add("table-row");

        for (let i of itemColumns) {
            if (!stock && i === 'AvailableStock') continue;

            let y = x[i];
            let td = document.createElement("div");
            
            if (i === "Price") {
                let t0 = document.createElement("div");
                t0.classList.add("currency");
                let [t1, t2] = [document.createElement("span"), document.createElement("span")];
                t1.innerHTML = y[0];
                t2.innerHTML = y.slice(1);
                t0.appendChild(t1);
                t0.appendChild(t2);
                td.appendChild(t0);
            } else td.innerHTML = y;

            if (i === "ItemID") td.classList.add("mono");
            if (i === "ItemDescription") td.classList.add("left");
            if (i === "Price") td.classList.add("tabnum");
            if (i === "AvailableStock" && y === "0") td.classList.add("red");

            tr.appendChild(td);
        }
        
        if (buttons) {
            let e = document.createElement("div");
            let b = document.createElement("button");
            b.type = "button";
            b.role = "button";
            b.innerHTML = "<i class='bi bi-plus-circle'></i><i class='bi bi-plus-circle-fill'></i>";
            b.classList.add("select-row");
            if (requesting && x['AvailableStock'] === "0") b.disabled = true;
            e.appendChild(b);
            tr.appendChild(e);
        }

        tbody.appendChild(tr);
        rows.push(tr);
    }

    tbody.querySelector(".table-loading").classList.add("hide");
    if (items.length > 0) tbody.querySelector(".table-empty").classList.add("hide");
    else tbody.querySelector(".table-empty").classList.remove("hide");

    document.dispatchEvent(new CustomEvent("tablerefresh"));

    return rows;
}

async function getRequests (keyword = "", type = "") {
    return fetch(encodeURI(`/requests/search?type=${type}${keyword === "" ? "" : "&keywords=" + escapeKeyword(keyword) + ""}`)).then(d => d.json()).then(j => j["requests"]);
}

async function populateRequests (tbody, keyword = "", type = "") {
    while (tbody.childElementCount > 2) tbody.removeChild(tbody.lastChild);

    tbody.querySelector(".table-loading").classList.remove("hide");
    tbody.querySelector(".table-empty").classList.add("hide");

    let requests = await getRequests(keyword, type);

    for (let req of requests) {
        let tr = document.createElement("div");
        tr.classList.add("table-row")

        for (let i of requestColumns.slice(0, 4)){
            if (!(i in req)) continue;

            let td = document.createElement("div");
            td.style.gridRow = `1 / ${req["Items"].length + 1}`;

            if (i === 'Status') {
                span = document.createElement("span")
                span.classList.add("status");
                span.classList.add(req[i].toLowerCase())
                span.innerText = req[i];
                td.appendChild(span);
            } else td.innerText = req[i];
            
            tr.appendChild(td);
        }

        let readyForIssue = 1;          // Used for approved requests page to check if all items checked
        let allItemsUnavailable = 1;    // Checks if all items are unavailable

        for (let j of req["Items"]) {
            for (let k of requestColumns.slice(4)) {
                let td = document.createElement("div");
                if (k === 'ItemID') td.classList.add("mono");
                if (k === 'ItemDescription') td.classList.add("left");
                if (k === 'AvailableStock' && +j['RequestQuantity'] > +j[k]) td.classList.add("red");
                td.innerText = j[k];
                
                tr.appendChild(td)
            }
            tr.appendChild(document.createElement("div")); // Temporary fix to easily add buttons at the rightmost

            // Generate buttons in Approved Requests page
            if (type == 'approved'){
                if (j["ItemIssued"] == null) {
                    readyForIssue = 0;
                    allItemsUnavailable = 0;
                    let btn = document.createElement("button");
                    btn.type = "button";
                    btn.innerText = "Available";
                    btn.classList.add("available-btn");
                    btn.value = req["RequestID"] + ' ' + j["ItemID"];

                    let btn2 = document.createElement("button");
                    btn2.type = "button";
                    btn2.innerText = "Not Available";
                    btn2.classList.add("not-available-btn");
                    btn2.value = req["RequestID"] + ' ' + j["ItemID"];

                    tr.lastChild.appendChild(btn);
                    tr.lastChild.appendChild(btn2);
                } else if (j["ItemIssued"]){
                    allItemsUnavailable = 0;
                    tr.lastChild.innerText = j["IssueAmount"];
                } else {
                    tr.lastChild.innerText = "Item Unavailable";
                }
                tr.appendChild(document.createElement("div"));
            }
        }

        if (type == 'approved'){
            if (allItemsUnavailable) {
                let btn = document.createElement("button");
                btn.innerText = "Cancel";
                btn.classList.add("cancel-issue-btn");
                btn.type = "button";
                btn.value = req["RequestID"];

                tr.lastChild.append(btn);
            } else if (readyForIssue){
                let btn = document.createElement("button");
                btn.innerText = "Issue";
                btn.classList.add("issue-btn");
                btn.type = "button";
                btn.value = req["RequestID"];

                tr.lastChild.append(btn);
            }
        }

        if (type == 'pending'){
            let td = tr.lastChild // Temporary fix to easily add buttons at the rightmost

            let approveBtn = document.createElement("button");
            approveBtn.innerText = "Approve";
            approveBtn.classList.add("approve-btn");
            approveBtn.type = "button";
            approveBtn.value = req["RequestID"];

            let denyBtn = document.createElement("button");
            denyBtn.innerText = "Deny";
            denyBtn.classList.add("deny-btn");
            denyBtn.type = "button";
            denyBtn.value = req["RequestID"];

            td.appendChild(approveBtn);
            td.appendChild(denyBtn);

            tr.appendChild(td);
        }

        if (type == "user" && req["Status"] != "Cancelled" && req["Status"] != "Rejected" && req["Status"] != "Completed"){
            let td = tr.lastChild; // Temporary fix to easily add buttons at the rightmost
            let btn = document.createElement("button");
            btn.type = "button";
            btn.value = req["RequestID"];
            if (req["Status"] == "Issued"){
                btn.classList.add("receive-btn");
                btn.innerText = "Receive";
                
            } else {
                btn.classList.add("cancel-btn");
                btn.innerText = "Cancel";
            }

            td.append(btn);
            tr.appendChild(td);
        }

        tbody.appendChild(tr);
    }

    tbody.querySelector(".table-loading").classList.add("hide");
    if (requests.length > 0) tbody.querySelector(".table-empty").classList.add("hide");
    else tbody.querySelector(".table-empty").classList.remove("hide");

    document.dispatchEvent(new CustomEvent("tablerefresh"));
}

async function getDeliveries (keyword = "") {
    return fetch(encodeURI(`/deliveries/search${keyword === "" ? "" : "?keywords=" + escapeKeyword(keyword)}`)).then(d => d.json()).then(j => j["deliveries"]);
}

async function populateDeliveries (tbody, keyword = "") {
    while (tbody.childElementCount > 2) tbody.removeChild(tbody.lastChild);

    tbody.querySelector(".table-loading").classList.remove("hide");
    tbody.querySelector(".table-empty").classList.add("hide");

    let items = await getDeliveries(keyword);

    for (let x of items) {
        let tr = document.createElement("div");
        tr.classList.add("table-row");

        for (let i of deliveryColumns) {
            let y = x[i];
            let td = document.createElement("div");

            if (i === 'IsExpired') {
                if (y) {
                    let span = document.createElement("span");
                    span.classList.add("status");
                    span.classList.add("expired");
                    span.innerText = "expired";
                    td.appendChild(span);
                }
            } else td.innerText = y;

            if (i === "ItemID") td.classList.add("mono");
            if (i === "ItemDescription") td.classList.add("left");

            tr.appendChild(td);
        }

        tbody.appendChild(tr);
    }

    tbody.querySelector(".table-loading").classList.add("hide");
    if (items.length > 0) tbody.querySelector(".table-empty").classList.add("hide");
    else tbody.querySelector(".table-empty").classList.remove("hide");

    document.dispatchEvent(new CustomEvent("tablerefresh"));
}

function sortTable (table, column, currentSort, { shelfLife = false, numerical = false, date = false } = {}) {
    let oldSym = table.querySelector(`.table-header .table-row > :nth-child(${currentSort[0] + 1}) .bi`);
    oldSym.classList.remove(`bi-chevron-${currentSort[1] ? "up" : "down"}`);
    oldSym.classList.add("bi-chevron-expand");
    
    let tbody = table.querySelector(".table-body");

    let rows = Array.from(tbody.querySelectorAll(".table-row:not(.hide)"));
    currentSort = [column, column === currentSort[0] ? !currentSort[1] : true];
    rows.sort((a, b) => {
        let [x, y] = [a.children[column].innerText, b.children[column].innerText];
        let desc = currentSort[1] ? 1 : -1;
        let s;

        if (shelfLife) {
            s = desc * (+x - +y);
            if (Number.isNaN(s)) s = +(x === '\u2014') + -(y === '\u2014');
        } else if (numerical) s = desc * (+x - +y);
        else if (date) {
            let [v, w] = [new Date(x), new Date(y)]
            let vs = `${v.getFullYear()}-${(v.getMonth() + 1).toString().padStart(2, "0")}-${(v.getDate()).toString().padStart(2, "0")}`;
            let ws = `${w.getFullYear()}-${(w.getMonth() + 1).toString().padStart(2, "0")}-${(w.getDate()).toString().padStart(2, "0")}`;
            s = desc * (vs.localeCompare(ws));
        } else s = desc * (x.localeCompare(y));

        return s === 0 ? a.children[0].innerText.localeCompare(b.children[0].innerText) : s;
    });

    while (tbody.childElementCount > 2) tbody.removeChild(tbody.lastChild);
    for (let row of rows) tbody.appendChild(row);
    
    let newSym = table.querySelector(`.table-header .table-row > :nth-child(${currentSort[0] + 1}) .bi`);
    newSym.classList.remove("bi-chevron-expand");
    newSym.classList.add(`bi-chevron-${currentSort[1] ? "up" : "down"}`);

    return currentSort;
}

async function decidePendingRequest(decision, requestID){
    fetch(encodeURI(`/requests/pendingRequests/decide`), {
        "method": "POST",
        "headers": {
            "Content-Type": "application/json"
        }, 
        "body":JSON.stringify({
            "decision": decision,
            "requestID": requestID
        })
    }).then(d => {
        if (d.status === 200) return;
    });
}

async function cancelRequest(requestID){
    fetch(encodeURI(`/requests/cancel`), {
        "method": "POST",
        "headers": {
            "Content-Type": "application/json"
        }, 
        "body":JSON.stringify({
            "requestID": requestID
        })
    }).then(d => {
        if (d.status === 200) return;
    });
}

async function receiveRequest(requestID){
    fetch(encodeURI(`/requests/receive`), {
        "method": "POST",
        "headers": {
            "Content-Type": "application/json"
        }, 
        "body":JSON.stringify({
            "requestID": requestID
        })
    }).then(d => {
        if (d.status === 200) return;
    });
}

async function issueRequestItem(decision = 1, amount = 0, requestID = "", itemID = ""){
    fetch(encodeURI(`/requests/approvedRequests/issue/item`), {
        "method": "POST",
        "headers": {
            "Content-Type": "application/json"
        }, 
        "body":JSON.stringify({
            "decision": decision,
            "amount": amount,
            "RequestID": requestID,
            "ItemID": itemID
        })
    }).then(d => {
        if (d.status === 200) return;
    });
}

async function issueRequest(requestID){
    fetch(encodeURI(`/requests/approvedRequests/issue`), {
        "method": "POST",
        "headers": {
            "Content-Type": "application/json"
        }, 
        "body":JSON.stringify({
            "requestID": requestID
        })
    }).then(d => {
        if (d.status === 200) return;
    });
}