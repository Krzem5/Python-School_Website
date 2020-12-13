document.addEventListener("DOMContentLoaded",()=>{
	let te=document.querySelector(".title");
	let mne=document.querySelector(".main");
	let aie=document.querySelector(".s-inp");
	let ae=document.querySelector(".list");
	let aue=document.querySelector(".user-wr");
	let le=document.querySelector(".logs");
	let s=null;
	let t;
	let tm;
	function _start_socket(){
		fetch("/api/v1/admin/logs",{headers:{"authorization":`bearer ${localStorage._tk}`}}).catch((e)=>0).then((e)=>(e?e.json():0)).then((e)=>{
			if (!e||e.status){
				location.reload();
			}
			s=new WebSocket(`wss://krzem.herokuapp.com/api/v1/admin/logs/${e.url}`);
			s.onclose=()=>{
				if (s){
					_start_socket();
				}
			}
			s.onmessage=(e)=>{
				e.data.text().then((e)=>{
					if (e=="null"){
						return;
					}
					t=e[0];
					e=e.substring(1);
					if (t==0){
						tm=e.split("]")[0];
						le.innerHTML+=`<div class="msg"><span class="t">${tm}]</span><span class="m">${e.substring(tm.length+1)}</span></div>`;
					}
					else{
						for (let k of e.split("\n")){
							tm=k.split("] ")[0];
							le.innerHTML+=`<div class="msg"><span class="t">${tm}] </span><span class="m">${k.substring(tm.length+2)}</span></div>`;
						}
					}
					le.scroll(0,le.scrollHeight);
				});
			}
			s.onerror=(e)=>{
				e.stopImmediatePropagation();
				e.stopPropagation();
				e.preventDefault();
			}
		});
	}
	te.innerHTML=te.innerText.split("").map((e)=>{
		return `<span class="c">${e}</span>`;
	}).join("");
	document.querySelector(".icon").onclick=()=>{
		location.href="/";
	}
	window.switch=(id)=>{
		if (window.s==id){
			return;
		}
		aie.value="";
		// ae.innerHTML="";
		le.innerHTML="";
		mne.classList.remove(`id${window.s}`);
		mne.classList.add(`id${id}`);
		window.s=id;
		if (s){
			let ts=s;
			s=null;
			ts.close();
		}
		if (id==2){
			_start_socket();
		}
	}
	window.switch(0);
	window.show=(nm,em,id,tm,ip,tk,tke,img,pwd,ev,a,d)=>{
		aue.classList.add("s");
		aue.innerHTML=`<div class="user"><div class="u-elem"><span class="k">Name:</span><span class="v nm" onclick="window.copy(this)">${nm}</span></div><div class="u-elem"><span class="k">Email:</span><span class="v em" onclick="window.copy(this)">${em}</span></div><div class="u-elem"><span class="k">ID:</span><span class="v id" onclick="window.copy(this)">${id}</span></div><div class="u-elem"><span class="k">Join Date:</span><span class="v tm" onclick="window.copy(this)">${tm}</span></div><div class="u-elem"><span class="k">Join IP:</span><span class="v ip" onclick="window.copy(this)">${ip}</span></div><div class="u-elem"><span class="k">Log-In Token:</span><span class="v tk" onclick="window.copy(this)">${(tk?tk+" ("+tke+")":"none")}</span></div><div class="u-elem"><span class="k">Image:</span><span class="v img" onclick="window.copy(this)">${img}</span></div><div class="u-elem"><span class="k">Password:</span><span class="v pwd" onclick="window.copy(this)">${pwd}</span></div><div class="u-elem"><span class="k">Tags:</span><span class="v tg" onclick="window.copy(this)"><span class="${(d?"s":"")}">disabled</span> <span class="${(tk?"s":"")}">logged-in</span> <span class="${(ev?"s":"")}">verified-email</span> <span class="${(a?"s":"")}">admin</span></span></div><input class="ch-nm" type="text" placeholder="Name" value="${nm}" minlength="3" maxlength="24"></div>`;
		t=document.querySelector(".ch-nm");
		t.onkeyup=(e)=>{
			if (e.keyCode==13){
				fetch("/api/v1/admin/set_name",{method:"PUT",headers:{"authorization":`bearer ${localStorage._tk}`},body:JSON.stringify({id:id,name:t.value})}).catch((e)=>0).then((e)=>(e?e.json():0)).then((e)=>{
					if (e&&!e.status){
						aue.classList.remove("s");
						aie.onkeyup();
					}
				});
			}
		}
	}
	window.copy=(e)=>{
		navigator.clipboard.writeText(e.innerText);
	}
	document.body.onkeydown=(e)=>{
		if (e.keyCode==27){
			aue.classList.remove("s");
		}
	}
	aie.onkeyup=(e)=>{
		function pad(n){
			n=Number(n).toString();
			if (n.length<2){
				n="0"+n;
			}
			return n;
		}
		if (!e||e.keyCode==13){
			fetch("/api/v1/admin/users",{method:"POST",headers:{"authorization":`bearer ${localStorage._tk}`},body:JSON.stringify({query:aie.value})}).catch((e)=>0).then((e)=>(e?e.json():0)).then((e)=>{
				if (!e||e.status){
					console.log("FAIL FETCH");
				}
				else{
					ae.innerHTML="";
					for (let k of e.users){
						let d=new Date(k.time*1000);
						let td=new Date(k.token_end*1000);
						ae.innerHTML+=`<div class="l-elem" onclick="window.show('${k.username}','${k.email}','${k.id}','${pad(d.getMonth()+1)}/${pad(d.getDate())}/${d.getFullYear()} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())} (${k.time})','${k.ip}',${(k.token?"\'"+k.token+"\'":null)},'${pad(td.getMonth()+1)}/${pad(td.getDate())}/${td.getFullYear()} ${pad(td.getHours())}:${pad(td.getMinutes())}:${pad(td.getSeconds())} (${k.token_end})','${k.image}','${k.password}',${k.email_verified},${k.admin},${k.disabled})"><div class="pr"><span class="nm">${k.username}</span><span class="em">${k.email}</span></div></div>`;
					}
				}
			});
		}
	}
	fetch("/api/v1/admin",{headers:{"authorization":`bearer ${localStorage._tk}`}}).catch((e)=>0).then((e)=>(e?e.json():0)).then((e)=>{
		if (!e||e.status){
			location.href="/";
		}
		else{
			document.body.classList.remove("h");
		}
	});
},false);