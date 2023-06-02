const timeConv = {
    "days": 1,
    "weeks": 7,
    "months": 30,
    "years": 365,
    "N/A": -1
};

const itemColumns = ["ItemID", "ItemName", "ItemDescription", "ShelfLife", "Price", "AvailableStock", "Unit"];
const requestColumns = ["RequestID", "RequestedBy", "RequestDate", "Status", "ItemID", "ItemName", "ItemDescription", "RequestQuantity", "QuantityIssued", "AvailableStock", "Unit"];
const deliveryColumns = ["DeliveryID", "ItemID", "ItemName", "ItemDescription", "DeliveryQuantity", "Unit", "ShelfLife", "DeliveryDate", "ReceivedBy", "IsExpired"];
const userColumns = ["Username", "FirstName", "LastName", "Email", "Role"];

// converts escaped characters in keywords
function escapeKeyword (k) {
    return k.replaceAll(/[\u2018\u2019\u201c\u201d]/gu, x => (x === '\u2018' || x === '\u2019') ? '"' : "'").replaceAll(/[:/?#\[\]@!$&'()*+,;=%]/g, x => "%" + x.charCodeAt(0).toString(16).toUpperCase());
}

// fetches users from database
async function getUsers (keyword = "") {
    return fetch(encodeURI(`/users/search${keyword === "" ? "" : "?keywords=" + escapeKeyword(keyword)}`))
    .then(d => {
        if(d.status == 200){
            return d.json().then(j => j["users"]);
        }
        else{
            return -1;
        }
    });
}

// populates user table with users from getUsers()
async function populateUsers (tbody, keyword = "", type="users") {
    while (tbody.childElementCount > 3) tbody.removeChild(tbody.lastChild);

    tbody.querySelector(".table-loading").classList.remove("hide");
    tbody.querySelector(".table-empty").classList.add("hide");

    let users = await getUsers(keyword);

    if(users == -1){
        tbody.querySelector(".table-error").classList.remove("hide");
        tbody.querySelector(".table-loading").classList.add("hide");
        return;
    }

    let rows = [];

    for (let user of users) {
        if(user['Role'] === 'Admin'){
            continue;
        }
        
        let tr = document.createElement("div");
        tr.classList.add("table-row");

        for (let i of userColumns) {
            let y = user[i];
            let td = document.createElement("div");
            
            td.innerHTML = y;

            tr.appendChild(td);
        }

        if(type == "users"){
            let div = document.createElement("div");
            let btn = document.createElement("button");
            btn.type = "button";
            btn.role = "button";

            if (user['Role'] === 'Custodian') {
                btn.title = "Demote user";
                btn.innerText = "Demote";
                btn.classList.add("red");

                btn.addEventListener("click", () => {
                    let modal = document.querySelector("#modal-users");

                    modal.showModal();
                    modal.querySelector("h1").innerText = "Demote user";
                    modal.querySelector("p").innerHTML = `<span>Are you sure you want to demote user <b>${user['Username']}</b> to Personnel?</span>`;
                    modal.querySelector("input[type=submit]").value = "Demote user";
                    modal.querySelector("input[type=submit]").classList.add("btn-red");
                    modal.querySelector("input[type=submit]").style.transitionDuration = '0s';
                    modal.querySelector("input[type=submit]").offsetHeight;
                    modal.querySelector("input[type=submit]").style.transitionDuration = '';

                    modal.querySelector("input[type=submit]").addEventListener("click", e => {
                        e.preventDefault();
                        
                        fetch("./demote", {
                            "method": "POST",
                            "headers": {
                                "Content-Type": "application/json"
                            },
                            "body": JSON.stringify({
                                "Username": user['Username']
                            })
                        }).then(d => {
                            if (d.status === 200) {
                                modal.close();
                                populateUsers(tbody, keyword);
                            }

                            if (d.status === 500){
                                d.json().then(a => {
                                    let p = modal.querySelector('.message')
                                    p.style.display = 'block'
                                    
                                    if(a["error"] == 2003){
                                        p.innerHTML = "Database error. Please try again later."
                                    }
                                    else{
                                        p.innerHTML = "Internal server error. Please try again later."
                                    }
                                });
                            }
                        })
                        .catch(() => {
                            let p = modal.querySelector('.message')
                            p.innerHTML = 'Server unavailable. Please try again later'
                            p.style.display = 'block'
                        });
                    });
                });
            }

            if (user['Role'] === 'Personnel') {
                btn.title = "Promote user";
                btn.innerText = "Promote";
                btn.classList.add("green");

                btn.addEventListener("click", () => {
                    let modal = document.querySelector("#modal-users");

                    modal.showModal();
                    modal.querySelector("h1").innerText = "Promote user";
                    modal.querySelector("p").innerHTML = `<span>Are you sure you want to promote user <b>${user['Username']}</b> to Custodian?</span>`;
                    modal.querySelector("input[type=submit]").value = "Promote user";
                    modal.querySelector("input[type=submit]").classList.add("btn-green");
                    modal.querySelector("input[type=submit]").style.transitionDuration = '0s';
                    modal.querySelector("input[type=submit]").offsetHeight;
                    modal.querySelector("input[type=submit]").style.transitionDuration = '';

                    modal.querySelector("input[type=submit]").addEventListener("click", e => {
                        e.preventDefault();
                        
                        fetch("./promote", {
                            "method": "POST",
                            "headers": {
                                "Content-Type": "application/json"
                            },
                            "body": JSON.stringify({
                                "Username": user['Username']
                            })
                        }).then(d => {
                            if (d.status === 200) {
                                modal.close();
                                populateUsers(tbody, keyword);
                            }

                            if (d.status === 500){
                                d.json().then(a => {
                                    let p = modal.querySelector('.message')
                                    p.style.display = 'block'
                                    
                                    if(a["error"] == 2003){
                                        p.innerHTML = "Database error. Please try again later."
                                    }
                                    else{
                                        p.innerHTML = "Internal server error. Please try again later."
                                    }
                                });
                            }
                        })
                        .catch(() => {
                            let p = modal.querySelector('.message')
                            p.innerHTML = 'Server unavailable. Please try again later'
                            p.style.display = 'block'
                        });
                    });
                });
            }

            div.appendChild(btn)
            tr.appendChild(div);

            tbody.appendChild(tr);
            rows.push(tr);
        }

        if(type == "user-search"){
            let e = document.createElement("div");
            let b = document.createElement("button");
            b.type = "button";
            b.role = "button";
            b.innerHTML = "<i class='bi bi-plus-circle'></i><i class='bi bi-plus-circle-fill'></i>";
            b.classList.add("select-row");
            e.appendChild(b);
            tr.appendChild(e);
            tbody.appendChild(tr);
        }
    }

    tbody.querySelector(".table-loading").classList.add("hide");
    if (users.length > 0) tbody.querySelector(".table-empty").classList.add("hide");
    else tbody.querySelector(".table-empty").classList.remove("hide");

    document.dispatchEvent(new Event("tablerefresh"));

    return rows;
}

// fetches items from database
async function getItems (keyword = "") {
    return fetch(encodeURI(`/inventory/search${keyword === "" ? "" : "?keywords=" + escapeKeyword(keyword)}`))
    .then(d => {
        if(d.status == 200){
            return d.json().then(j => j["items"]);
        }
        else{
            return -1;
        }
    });
}

// populates item table with items from getItems()
async function populateItems (tbody, keyword = "", { stock = true, buttons = false, requesting = false } = {}) {
    while (tbody.childElementCount > 3) tbody.removeChild(tbody.lastChild);

    tbody.querySelector(".table-loading").classList.remove("hide");
    tbody.querySelector(".table-empty").classList.add("hide");

    let items = await getItems(keyword);
    if(items == -1){
        tbody.querySelector(".table-error").classList.remove("hide");
        tbody.querySelector(".table-loading").classList.add("hide");
        return;
    }

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

    document.dispatchEvent(new Event("tablerefresh"));

    return rows;
}

// fetches requests from database
async function getRequests (keyword = "", filter = []) {
    return fetch(encodeURI(`/requests/search${keyword === "" ? "" : "&keywords=" + escapeKeyword(keyword) + ""}${filter.length === 0 ? "" : "&filter=" + filter.join(",")}`.replace("&", "?")))
    .then(d => {
        if(d.status == 200){
            return d.json().then(j => j["requests"]);
        }
        else{
            return -1;
        }
    });
}

// populates request table with requests from getRequests()
async function populateRequests (tbody, keyword = "", privileges = "user", filter = undefined) {
    while (tbody.childElementCount > 3) tbody.removeChild(tbody.lastChild);

    tbody.querySelector(".table-loading").classList.remove("hide");
    tbody.querySelector(".table-empty").classList.add("hide");

    let requests = await getRequests(keyword, filter);
    let rows = [];
    if(requests == -1){
        tbody.querySelector(".table-error").classList.remove("hide");
        tbody.querySelector(".table-loading").classList.add("hide");
        return;
    }
    
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

        for (let j of req["Items"]) {
            for (let k of requestColumns.slice(4)) {
                if (k === 'RequestedBy' && !custodian) continue;

                let td = document.createElement("div");
                if (k === 'ItemID') td.classList.add("mono");
                if (k === 'ItemDescription') td.classList.add("left");
                if (k === 'AvailableStock' && +j['RequestQuantity'] > +j[k]) td.classList.add("red");
                td.innerText = j[k];
                
                tr.appendChild(td)
            }
            
            if (privileges === 1 && req["Items"].map(x => x['QuantityIssued']).some(x => x === '\u2014')) {
                let div = document.createElement("div");

                if (req['Status'] === 'Approved' && j['QuantityIssued'] === '\u2014') {
                    let btn = document.createElement("button");
                    btn.classList.add("issue");
                    btn.type = "button";
                    btn.role = "button";
                    btn.title = "Issue item";
                    btn.innerHTML = "<i class='bi bi-box-seam'></i>";

                    btn.addEventListener("click", () => {
                        let modal = document.querySelector("#modal-requests");

                        modal.showModal();
                        modal.querySelector("h1").innerText = "Issue item";
                        modal.querySelector("p").style.display = "none";
                        modal.querySelector("#quantity-span").style.display = "";
                        modal.querySelector("input[type=number]").focus();
                        modal.querySelector("input[type=number]").min = 0;
                        modal.querySelector("input[type=number]").max = Math.min(+j['AvailableStock'].replace(",", ""), +j['RequestQuantity'].replace(",", ""));
                        modal.querySelector("input[type=number]").step = 1;
                        modal.querySelector("input[type=number]").value = Math.min(+j['AvailableStock'].replace(",", ""), +j['RequestQuantity'].replace(",", ""));
                        modal.querySelector("input[type=number] ~ span").innerText = j['Unit'];
                        modal.querySelector("input[type=submit]").value = "Issue item";

                        modal.querySelector("input[type=submit]").addEventListener("click", e => {
                            e.preventDefault();
                            
                            fetch("./issue/item", {
                                "method": "POST",
                                "headers": {
                                    "Content-Type": "application/json"
                                },
                                "body": JSON.stringify({
                                    "RequestID": req['RequestID'],
                                    "ItemID": j['ItemID'],
                                    "QuantityIssued": +modal.querySelector("input[type=number]").value
                                })
                            }).then(d => {
                                if (d.status === 200) {
                                    modal.close();
                                    populateRequests(tbody, keyword, privileges, filter);
                                }

                                if (d.status === 500){
                                    d.json().then(a => {
                                        let p = modal.querySelector('.message')
                                        p.style.display = 'block'
                                        
                                        if(a["error"] == 2003){
                                            p.innerHTML = "Database error. Please try again later."
                                        }
                                        else{
                                            p.innerHTML = "Internal server error. Please try again later."
                                        }
                                    });
                                }
                            })
                            .catch(() => {
                                let p = modal.querySelector('.message')
                                p.innerHTML = 'Server unavailable. Please try again later'
                                p.style.display = 'block'
                            });
                        });
                    });

                    div.appendChild(btn);
                }

                tr.appendChild(div);
            }
        }
        
        let actions = document.createElement("div");
        actions.classList.add("actions");
        actions.style.gridColumn = '-1 / -2';
        actions.style.gridRow = `1 / ${req["Items"].length + 1}`;
        
        if (req['Status'] === 'Approved' && privileges === 1) {
            if (req["Items"].map(x => x['QuantityIssued']).every(x => x !== '\u2014')) {
                actions.style.gridColumn = '-1 / -3';

                let issueBtn = document.createElement("button");
                issueBtn.type = "button";
                issueBtn.role = "button";
                issueBtn.title = "Issue requested items";
                issueBtn.innerHTML = "<i class='bi bi-check-circle'></i>";
                issueBtn.classList.add("green");

                issueBtn.addEventListener("click", () => {
                    let modal = document.querySelector("#modal-requests");

                    modal.showModal();
                    modal.querySelector("h1").innerText = "Issue request";
                    modal.querySelector("p").innerHTML = "<span>Are you sure you want to issue <b>all</b> items in this request?</span>";
                    modal.querySelector("input[type=submit]").value = "Issue request";
                    modal.querySelector("input[type=submit]").classList.add("btn-green");
                    modal.querySelector("input[type=submit]").style.transitionDuration = '0s';
                    modal.querySelector("input[type=submit]").offsetHeight;
                    modal.querySelector("input[type=submit]").style.transitionDuration = '';

                    modal.querySelector("input[type=submit]").addEventListener("click", e => {
                        e.preventDefault();
                        
                        fetch("./issue", {
                            "method": "POST",
                            "headers": {
                                "Content-Type": "application/json"
                            },
                            "body": JSON.stringify({
                                "RequestID": req['RequestID']
                            })
                        }).then(d => {
                            if (d.status === 200) {
                                modal.close();
                                populateRequests(tbody, keyword, privileges, filter);
                            }

                            if (d.status === 500){
                                d.json().then(a => {
                                    let p = modal.querySelector('.message')
                                    p.style.display = 'block'
                                    
                                    if(a["error"] == 2003){
                                        p.innerHTML = "Database error. Please try again later."
                                    }
                                    else{
                                        p.innerHTML = "Internal server error. Please try again later."
                                    }
                                });
                            }
                        })
                        .catch(() => {
                            let p = modal.querySelector('.message')
                            p.innerHTML = 'Server unavailable. Please try again later'
                            p.style.display = 'block'
                        });
                    });
                });

                actions.append(issueBtn);
            }
            
            let cancelBtn = document.createElement("button");
            cancelBtn.type = "button";
            cancelBtn.role = "button";
            cancelBtn.title = "Cancel request";
            cancelBtn.innerHTML = "<i class='bi bi-x-circle'></i>";
            cancelBtn.classList.add("red");

            cancelBtn.addEventListener("click", () => {
                let modal = document.querySelector("#modal-requests");

                modal.showModal();
                modal.querySelector("h1").innerText = "Cancel request";
                modal.querySelector("p").innerHTML = "Are you sure you want to cancel this request?<br><i><b style='color: var(--red);'>WARNING:</b> This will forfeit <b>all</b> items in this request!</i>";
                modal.querySelector("input[type=submit]").value = "Cancel request";
                modal.querySelector("input[type=submit]").classList.add("btn-red");
                modal.querySelector("input[type=submit]").style.transitionDuration = '0s';
                modal.querySelector("input[type=submit]").offsetHeight;
                modal.querySelector("input[type=submit]").style.transitionDuration = '';

                modal.querySelector("input[type=submit]").addEventListener("click", e => {
                    e.preventDefault();

                    fetch("./cancel", {
                        "method": "POST",
                        "headers": {
                            "Content-Type": "application/json"
                        },
                        "body": JSON.stringify({
                            "RequestID": req['RequestID']
                        })
                    }).then(d => {
                        if (d.status === 200) {
                            modal.close();
                            populateRequests(tbody, keyword, privileges, filter);
                        }

                        if (d.status === 500){
                            d.json().then(a => {
                                let p = modal.querySelector('.message')
                                p.style.display = 'block'
                                
                                if(a["error"] == 2003){
                                    p.innerHTML = "Database error. Please try again later."
                                }
                                else{
                                    p.innerHTML = "Internal server error. Please try again later."
                                }
                            });
                        }
                    })
                    .catch(() => {
                        let p = modal.querySelector('.message')
                        p.innerHTML = 'Server unavailable. Please try again later'
                        p.style.display = 'block'
                    });
                });
            });

            actions.append(cancelBtn);
        }
        
        if (req['Status'] === 'Pending' && privileges === 0) {
            let approveBtn = document.createElement("button");
            approveBtn.title = "Approve request";
            approveBtn.type = "button";
            approveBtn.role = "button";
            approveBtn.value = req["RequestID"];
            approveBtn.innerHTML = "<i class='bi bi-check-circle'></i>";
            approveBtn.classList.add("green");

            approveBtn.addEventListener("click", () => {
                let modal = document.querySelector("#modal-requests");

                modal.showModal();
                modal.querySelector("h1").innerText = "Approve request";
                modal.querySelector("p").innerHTML = "Are you sure you want to approve this request?";
                modal.querySelector("input[type=submit]").value = "Approve request";
                modal.querySelector("input[type=submit]").classList.add("btn-green");
                modal.querySelector("input[type=submit]").style.transitionDuration = '0s';
                modal.querySelector("input[type=submit]").offsetHeight;
                modal.querySelector("input[type=submit]").style.transitionDuration = '';

                modal.querySelector("input[type=submit]").addEventListener("click", e => {
                    e.preventDefault();

                    fetch("./approve", {
                        "method": "POST",
                        "headers": {
                            "Content-Type": "application/json"
                        },
                        "body": JSON.stringify({
                            "RequestID": req['RequestID']
                        })
                    }).then(d => {
                        if (d.status === 200) {
                            modal.close();
                            populateRequests(tbody, keyword, privileges, filter);
                        }

                        if (d.status === 500){
                            d.json().then(a => {
                                let p = modal.querySelector('.message')
                                p.style.display = 'block'
                                
                                if(a["error"] == 2003){
                                    p.innerHTML = "Database error. Please try again later."
                                }
                                else{
                                    p.innerHTML = "Internal server error. Please try again later."
                                }
                            });
                        }
                    })
                    .catch(() => {
                        let p = modal.querySelector('.message')
                        p.innerHTML = 'Server unavailable. Please try again later'
                        p.style.display = 'block'
                    });
                });
            });

            let denyBtn = document.createElement("button");
            denyBtn.title = "Deny request";
            denyBtn.type = "button";
            denyBtn.role = "button";
            denyBtn.value = req["RequestID"];
            denyBtn.innerHTML = "<i class='bi bi-x-circle'></i>";
            denyBtn.classList.add("red");

            denyBtn.addEventListener("click", () => {
                let modal = document.querySelector("#modal-requests");

                modal.showModal();
                modal.querySelector("h1").innerText = "Deny request";
                modal.querySelector("p").innerHTML = "Are you sure you want to deny this request?";
                modal.querySelector("input[type=submit]").value = "Deny request";
                modal.querySelector("input[type=submit]").classList.add("btn-red");
                modal.querySelector("input[type=submit]").style.transitionDuration = '0s';
                modal.querySelector("input[type=submit]").offsetHeight;
                modal.querySelector("input[type=submit]").style.transitionDuration = '';

                modal.querySelector("input[type=submit]").addEventListener("click", e => {
                    e.preventDefault();
                    
                    fetch("./deny", {
                        "method": "POST",
                        "headers": {
                            "Content-Type": "application/json"
                        },
                        "body": JSON.stringify({
                            "RequestID": req['RequestID']
                        })
                    }).then(d => {
                        if (d.status === 200) {
                            modal.close();
                            populateRequests(tbody, keyword, privileges, filter);
                        }

                        if (d.status === 500){
                            d.json().then(a => {
                                let p = modal.querySelector('.message')
                                p.style.display = 'block'
                                
                                if(a["error"] == 2003){
                                    p.innerHTML = "Database error. Please try again later."
                                }
                                else{
                                    p.innerHTML = "Internal server error. Please try again later."
                                }
                            });
                        }
                    })
                    .catch(() => {
                        let p = modal.querySelector('.message')
                        p.innerHTML = 'Server unavailable. Please try again later'
                        p.style.display = 'block'
                    });
                });
            });
            
            actions.appendChild(approveBtn);
            actions.appendChild(denyBtn);
        }
        
        if (privileges === 2 && ['Pending', 'Approved', 'Issued'].includes(req['Status'])) {
            if (req['Status'] === 'Issued') {
                let receiveBtn = document.createElement("button");
                receiveBtn.title = "Receive requested items";
                receiveBtn.type = "button";
                receiveBtn.role = "button";
                receiveBtn.value = req["RequestID"];
                receiveBtn.innerHTML = "<i class='bi bi-check-circle'></i>";
                receiveBtn.classList.add("green");
                
                receiveBtn.addEventListener("click", () => {
                    let modal = document.querySelector("#modal-requests");

                    modal.showModal();
                    modal.querySelector("h1").innerText = "Receive request";
                    modal.querySelector("p").innerHTML = "Are you sure you want to receive this request?";
                    modal.querySelector("input[type=submit]").value = "Receive request";
                    modal.querySelector("input[type=submit]").classList.add("btn-green");
                    modal.querySelector("input[type=submit]").style.transitionDuration = '0s';
                    modal.querySelector("input[type=submit]").offsetHeight;
                    modal.querySelector("input[type=submit]").style.transitionDuration = '';

                    modal.querySelector("input[type=submit]").addEventListener("click", e => {
                        e.preventDefault();
                        
                        fetch("./receive", {
                            "method": "POST",
                            "headers": {
                                "Content-Type": "application/json"
                            },
                            "body": JSON.stringify({
                                "RequestID": req['RequestID']
                            })
                        }).then(d => {
                            if (d.status === 200) {
                                modal.close();
                                populateRequests(tbody, keyword, privileges, filter);
                            }

                            if (d.status === 500){
                                d.json().then(a => {
                                    let p = modal.querySelector('.message')
                                    p.style.display = 'block'
                                    
                                    if(a["error"] == 2003){
                                        p.innerHTML = "Database error. Please try again later."
                                    }
                                    else{
                                        p.innerHTML = "Internal server error. Please try again later."
                                    }
                                });
                            }
                        })
                        .catch(() => {
                            let p = modal.querySelector('.message')
                            p.innerHTML = 'Server unavailable. Please try again later'
                            p.style.display = 'block'
                        });
                    });
                });

                actions.append(receiveBtn);
            }

            let cancelBtn = document.createElement("button");
            cancelBtn.title = "Cancel request";
            cancelBtn.type = "button";
            cancelBtn.role = "button";
            cancelBtn.value = req["RequestID"];
            cancelBtn.innerHTML = "<i class='bi bi-x-circle'></i>";
            cancelBtn.classList.add("red");

            cancelBtn.addEventListener("click", () => {
                let modal = document.querySelector("#modal-requests");

                modal.showModal();
                modal.querySelector("h1").innerText = "Cancel request";
                modal.querySelector("p").innerHTML = "Are you sure you want to cancel this request?<br><i><b style='color: var(--red);'>WARNING:</b> This will forfeit <b>all</b> items in this request!</i>";
                modal.querySelector("input[type=submit]").value = "Cancel request";
                modal.querySelector("input[type=submit]").classList.add("btn-red");
                modal.querySelector("input[type=submit]").style.transitionDuration = '0s';
                modal.querySelector("input[type=submit]").offsetHeight;
                modal.querySelector("input[type=submit]").style.transitionDuration = '';

                modal.querySelector("input[type=submit]").addEventListener("click", e => {
                    e.preventDefault();
                    
                    fetch("./cancel", {
                        "method": "POST",
                        "headers": {
                            "Content-Type": "application/json"
                        },
                        "body": JSON.stringify({
                            "RequestID": req['RequestID']
                        })
                    }).then(d => {
                        if (d.status === 200) {
                            modal.close();
                            populateRequests(tbody, keyword, privileges, filter);
                        }

                        if (d.status === 500){
                            d.json().then(a => {
                                let p = modal.querySelector('.message')
                                p.style.display = 'block'
                                
                                if(a["error"] == 2003){
                                    p.innerHTML = "Database error. Please try again later."
                                }
                                else{
                                    p.innerHTML = "Internal server error. Please try again later."
                                }
                            });
                        }
                    })
                    .catch(() => {
                        let p = modal.querySelector('.message')
                        p.innerHTML = 'Server unavailable. Please try again later'
                        p.style.display = 'block'
                    });
                });
            });

            actions.append(cancelBtn);
        }
        
        tr.appendChild(actions);
        tbody.appendChild(tr);
        rows.push(tr);
    }

    tbody.querySelector(".table-loading").classList.add("hide");
    if (requests.length > 0) tbody.querySelector(".table-empty").classList.add("hide");
    else tbody.querySelector(".table-empty").classList.remove("hide");

    document.dispatchEvent(new Event("tablerefresh"));

    return rows;
}

// fetches deliveries from database
async function getDeliveries (keyword = "") {
    return fetch(encodeURI(`/deliveries/search${keyword === "" ? "" : "?keywords=" + escapeKeyword(keyword)}`))
    .then(d => {
        if(d.status == 200){
            return d.json().then(j => j["deliveries"]);
        }
        else{
            return -1;
        }
    });
}

// populates delivery table with deliveries from getDeliveries()
async function populateDeliveries (tbody, keyword = "") {
    while (tbody.childElementCount > 3) tbody.removeChild(tbody.lastChild);

    tbody.querySelector(".table-loading").classList.remove("hide");
    tbody.querySelector(".table-empty").classList.add("hide");

    let items = await getDeliveries(keyword);
    if(items == -1){
        tbody.querySelector(".table-error").classList.remove("hide");
        tbody.querySelector(".table-loading").classList.add("hide");
        return;
    }

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

    document.dispatchEvent(new Event("tablerefresh"));
}

// sorts table based on column
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
