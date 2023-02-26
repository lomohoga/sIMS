const timeConv = {
    "minutes": 0.017,
    "hours": 1,
    "days": 24,
    "weeks": 168,
    "months": 720,
    "years": 8760,
    "N/A": -1
};

function escapeKeyword (k) {
    return k.replaceAll(/[\u2018\u2019\u201c\u201d]/gu, x => (x === '\u2018' || x === '\u2019') ? '"' : "'").replaceAll(/[:/?#\[\]@!$&'()*+,;=%]/g, x => "%" + x.charCodeAt(0).toString(16).toUpperCase());
}

async function getUsers (keyword = "") {
    return fetch(encodeURI("./search-users?keyword=" + escapeKeyword(keyword))).then(d => d.json()).then(j => j["users"]);
}

async function populateUsers(tbody, keyword = "", type = "users") {
    while (tbody.childElementCount > 2) tbody.removeChild(tbody.lastChild);

    tbody.querySelector(".table-loading").classList.remove("hide");
    tbody.querySelector(".table-empty").classList.add("hide");

    let users = await getUsers(keyword);

    for (let x of users) {
        let tr = document.createElement("div");
        tr.classList.add("table-row");

        for (let i = 0; i < 4; i++) {
            let y = x[i];
            let td = document.createElement("div");
            td.innerHTML = y
            tr.appendChild(td);
        }

        if(type === 'users'){
            let a = document.createElement("button");
            if(x[3] === "Personnel"){
                a.innerHTML = "Promote";
                a.addEventListener("click", () => {
                    fetch("/promote-user", {
                        "method": "POST",
                        "headers": {
                            "Content-Type": "application/json"
                        },
                        "body": JSON.stringify({ "values": x[0] })
                    }).then(d => {
                        if (d.status === 200) window.location = "/users";
                    });
                });
            }
            else{
                a.innerHTML = "Demote";
                a.addEventListener("click", () => {
                    fetch("/demote-user", {
                        "method": "POST",
                        "headers": {
                            "Content-Type": "application/json"
                        },
                        "body": JSON.stringify({ "values": x[0] })
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
    return fetch(encodeURI("./search?keyword=" + escapeKeyword(keyword))).then(d => d.json()).then(j => j["items"]);
}

async function populateTable (tbody, keyword = "", type = "inventory") {
    while (tbody.childElementCount > 2) tbody.removeChild(tbody.lastChild);

    tbody.querySelector(".table-loading").classList.remove("hide");
    tbody.querySelector(".table-empty").classList.add("hide");

    let items = await getItems(keyword);

    for (let x of items) {
        let tr = document.createElement("div");
        tr.classList.add("table-row");

        for (let i = 0; i < 7; i++) {
            let y = x[i];
            let td = document.createElement("div");
            
            if (i === 4) {
                let t0 = document.createElement("div");
                t0.classList.add("currency");
                let [t1, t2] = [document.createElement("span"), document.createElement("span")];
                t1.innerHTML = y[0];
                t2.innerHTML = y.slice(1);
                t0.appendChild(t1);
                t0.appendChild(t2);
                td.appendChild(t0);
            } else td.innerHTML = y;

            if (i === 0) td.classList.add("mono");
            if (i === 2) td.classList.add("left");
            if (i === 4 || i === 5) td.classList.add("tabnum");
            if (i === 5) td.classList.add("right");

            tr.appendChild(td);
        }

        if (type === 'delete') {
            let e = document.createElement("div");
            let c = document.createElement("input");
            c.type = "checkbox";
            e.appendChild(c);
            tr.insertBefore(e, tr.firstChild);
        } else if (type === 'item-search') {
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
    if (items.length > 0) tbody.querySelector(".table-empty").classList.add("hide");
    else tbody.querySelector(".table-empty").classList.remove("hide");

    document.dispatchEvent(new CustomEvent("tablerefresh"));
}

async function getRequests (keyword = "") {
    return fetch(encodeURI("./search-requests?keyword=" + escapeKeyword(keyword))).then(d => d.json()).then(j => j["requests"]);
}

async function populateRequests (tbody, keyword = "", custodian = true) {
    while (tbody.childElementCount > 2) tbody.removeChild(tbody.lastChild);

    tbody.querySelector(".table-loading").classList.remove("hide");
    tbody.querySelector(".table-empty").classList.add("hide");

    let items = await getRequests(keyword);

    for (let x of items) {
        let tr = document.createElement("div");
        tr.classList.add("table-row");

        for (let i = 0; i < 8; i++) {
            if (!custodian && i === 6) continue;

            let y = x[i];
            let td = document.createElement("div");
            td.innerHTML = i === 7 ? y.replaceAll("-", "\u2013") : y;

            if (y === null) {
                tr.classList.add("item-not-found");
                if (i === 2) {
                    td.innerHTML = "Item not found."
                    td.classList.add("extend");
                } else if (i === 3) continue;
            }

            if (i === 1) td.classList.add("mono");
            if (i === 3) td.classList.add("left");
            if (i === 4 || i === 6) td.classList.add("tabnum");
            if (i === 4) td.classList.add("right");

            tr.appendChild(td);
        }

        tbody.appendChild(tr);
    }

    tbody.querySelector(".table-loading").classList.add("hide");
    if (items.length > 0) tbody.querySelector(".table-empty").classList.add("hide");
    else tbody.querySelector(".table-empty").classList.remove("hide");

    document.dispatchEvent(new CustomEvent("tablerefresh"));
}
