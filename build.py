import sys
import os
import json
import shutil
import re
import tempfile
import time
import hashlib
import subprocess



BASE=f"{tempfile.gettempdir()}/heroku-build-{hashlib.sha1(bytes(os.getcwd(),'utf-8')).hexdigest()}".replace("/","\\")
with open("./secret.dt","r") as f:
	APP_NAME,EMAIL,USER_NAME=f.read().replace("\r","").split("\n")[:3]
JS_OPERATORS=["()=>","_=>","=>","...",">>>=",">>=","<<=","|=","^=","&=","+=","-=","*=","/=","%=",";",",","?",":","||","&&","|","^","&","===","==","=","!==","!=","<<","<=","<",">>>",">>",">=",">","++","--","+","-","*","/","%","!","~",".","[","]","{","}","(",")"]
JS_KEYWORDS=["break","case","catch","const","continue","debugger","default","delete","do","else","enum","false","finally","for","function","if","in","instanceof","new","null","return","switch","this","throw","true","try","typeof","var","void","while","with","let","var","const"]
JS_RESERVED_IDENTIFIERS=JS_KEYWORDS+["window","console","self","document","location","customElements","history","locationbar","menubar","personalbar","scrollbars","statusbar","toolbar","status","closed","frames","length","top","opener","parent","frameElement","navigator","origin","external","screen","innerWidth","innerHeight","scrollX","pageXOffset","scrollY","pageYOffset","visualViewport","screenX","screenY","outerWidth","outerHeight","devicePixelRatio","clientInformation","screenLeft","screenTop","defaultStatus","defaultstatus","styleMedia","isSecureContext","performance","crypto","indexedDB","sessionStorage","localStorage","alert","atob","blur","btoa","cancelAnimationFrame","cancelIdleCallback","captureEvents","clearInterval","clearTimeout","close","confirm","createImageBitmap","fetch","find","focus","getComputedStyle","getSelection","matchMedia","moveBy","moveTo","open","postMessage","print","prompt","queueMicrotask","releaseEvents","requestAnimationFrame","requestIdleCallback","resizeBy","resizeTo","scroll","scrollBy","scrollTo","setInterval","setTimeout","stop","webkitCancelAnimationFrame","webkitRequestAnimationFrame","chrome","caches","originIsolated","cookieStore","showDirectoryPicker","showOpenFilePicker","showSaveFilePicker","speechSynthesis","trustedTypes","crossOriginIsolated","openDatabase","webkitRequestFileSystem","webkitResolveLocalFileSystemURL"]
JS_VAR_LETTERS="abcdefghijklmnopqrstuvwxyz"
JS_CONST_LETTERS="ABCDEFGHIJKLMNOPQRSTUVWXYZ"
JS_REGEX_LIST={"regex":br"\/(?:\\.|\[(?:\\.|[^\]])*\]|[^\/])+\/[gimy]*","float":br"\d+\.\d*(?:[eE][-+]?\d+)?|^\d+(?:\.\d*)?[eE][-+]?\d+|^\.\d+(?:[eE][-+]?\d+)?","int":br"0[xX][\da-fA-F]+|^0[0-7]*|^\d+","identifier":br"[$_\w]+","string":br"""'(?:[^'\\]|\\.)*'|^"(?:[^"\\]|\\.)*"|^`(?:[^`\\]|\\.)*`""","operator":bytes("|".join([re.sub(r"([\?\|\^\&\(\)\{\}\[\]\+\-\*\/\.])",r"\\\1",e) for e in JS_OPERATORS]),"utf-8"),"line_break":br"[\n\r]+|/\*(?:.|[\r\n])*?\*/","whitespace":br"[\ \t]+|//.*?(?:[\r\n]|$)"}



def _minify_css(css,fp):
	sl=len(css)
	css=re.sub(br":\s*0(\.\d+(?:[cm]m|e[mx]|in|p[ctx]))\s*;",br":\1;",re.sub(br"#([0-9a-f])\1([0-9a-f])\2([0-9a-f])\3(\s|;)",br"#\1\2\3\4",re.sub(br"""url\(([\"'])([^)]*)\1\)""",br"url(\2)",re.sub(br"/\*[\s\S]*?\*/",b"",css))))
	i=0
	o=b""
	while (i<len(css)):
		m=re.match(br"\s*([^{]+?)\s*{",css[i:])
		if (m!=None):
			i+=m.end(0)+1
			b=1
			si=i-1
			while (b!=0):
				i+=1
				if (css[i:i+1]==b"{"):
					b+=1
				if (css[i:i+1]==b"}"):
					b-=1
			s=b",".join([re.sub(br"(?<=[\[\(>+=])\s+|\s+(?=[=~^$|>+\]\)])",b"",e.strip()) for e in m.group(1).split(b",")])
			if (re.split(br"\s",s)[0]==b"@keyframes"):
				v=[]
				l=[]
				t=[]
				for k in re.findall(br"\s*([^{]+?)\s*{\s*([^}]*?)\s*}",css[si:i]):
					v+=[{}]
					l+=[[]]
					t+=[k[0]]
					for e in re.findall(br"\s*(.*?)\s*:\s*(.*?)\s*(?:;|$)",k[1]):
						if (e[0].lower() not in l[-1]):
							l[-1]+=[e[0].lower()]
						v[-1][e[0].lower()]=e[1]
					if (len(l)==0):
						v=v[:-1]
						l=l[:-1]
						t=t[:-1]
				if (len(t)>0):
					o+=s+b"{"+b"".join([k+b"{"+b";".join([e+b":"+re.sub(br",\s+",b",",v[i][e]) for e in l[i]])+b";}" for i,k in enumerate(t)])+b"}"
			else:
				v={}
				l=[]
				for k in re.findall(br"\s*(.*?)\s*:\s*(.*?)\s*(?:;|$)",css[si:i].strip()):
					if (k[0].lower() not in l):
						l+=[k[0].lower()]
					v[k[0].lower()]=k[1]
				if (len(l)>0):
					o+=s+b"{"+b";".join([e+b":"+re.sub(br",\s+",b",",v[e]) for e in l])+b";}"
		i+=1
	print(f"Minified CSS File '{fp}': {sl} -> {len(o)} (-{round(10000-10000*len(o)/sl)/100}%)")
	return o
def _minify_js(js,fp):
	def _gen_i(il,b=JS_VAR_LETTERS):
		def _gen_next(v,b):
			o=""
			while (v>0):
				o=b[int(v%len(b))]+o
				v=v//len(b)
			return bytes(o,"utf-8")
		r=JS_RESERVED_IDENTIFIERS[:]
		for k in il:
			r+=k.values()
		i=0
		o=bytes(b[0],"utf-8")
		while (True):
			if (o not in r):
				break
			i+=1
			o=_gen_next(i,b)
		return o
	def _map_value(v,vml):
		for i in range(len(vml)-1,-1,-1):
			if (v in vml[i]):
				return vml[i][v]
		return None
	def _args(al):
		o=[]
		for k in al:
			if (len(o)>0):
				o+=[("operator",b",")]
			if (k[1]==True):
				o+=[("operator",b"...")]
			o+=[("identifier",k[0])]
		return o
	def _tokenize(s):
		i=0
		o=[]
		b=0
		while (i<len(s)):
			e=False
			for k,v in JS_REGEX_LIST.items():
				m=re.match(v,s[i:])
				if (m!=None):
					m=m.group(0)
					if (k=="line_break"):
						o+=[("operator",b";")]
					elif (k=="string" and m[:1]==b"`"):
						j=0
						ts=b""
						f=False
						while (j<len(m)):
							if (m[j:j+2]==b"${"):
								l,tj=_tokenize(m[j+2:])
								j+=tj+2
								o+=[("string"+("M" if f==True else "S"),ts)]+l
								ts=b""
								f=True
							else:
								ts+=m[j:j+1]
							j+=1
						o+=[("string"+("" if f==False else "E"),ts)]
					elif (k!="whitespace"):
						if (k=="identifier" and str(m,"utf-8") in JS_KEYWORDS):
							k="keyword"
						if (k=="operator"):
							if (m==b"{"):
								b+=1
							elif (m==b"}"):
								b-=1
								if (b==-1):
									return (o,i)
						o+=[(k,m)]
					i+=len(m)
					e=True
					break
			if (e==True):
				continue
			raise RuntimeError(f"ERROR: {s[i:]}")
		return (o,i)
	def _write(tl,cvm,cvma):
		o=b""
		i=0
		while (i<len(tl)):
			if (i>=len(sl) and tl[i][0]=="identifier"):
				idl=tl[i][1].split(b".")
				if (idl[0] in cvm):
					idl[0]=cvm[idl[0]]
				for j,e in enumerate(idl[1:]):
					if (e in cvma):
						idl[j+1]=b"["+cvma[e]+b"]"
					else:
						idl[j+1]=b"."+e
				o+=b"".join(idl)
			elif (tl[i][0]=="keyword" and tl[i][1] in [b"false",b"true"]):
				o+={b"false":b"!1",b"true":b"!0"}[tl[i][1]]
			elif (tl[i][0]=="stringS"):
				o+=tl[i][1]+b"${"
				to,ti=_write(tl[i+1:],cvm,cvm)
				o+=to
				i+=ti+1
			elif (tl[i][0]=="stringM"):
				o+=b"}"+tl[i][1]+b"${"
			elif (tl[i][0]=="stringE"):
				o+=b"}"+tl[i][1]
				break
			else:
				o+=tl[i][1]
				if (tl[i][0]=="keyword" and tl[i][1] in [b"let",b"const",b"var",b"return",b"throw"]):
					o+=b" "
			i+=1
		return (o,i)
	ofl=len(js)
	tl,_=_tokenize(js)
	i=0
	vm=[{}]
	cl=0
	ef=[]
	efbl={}
	ee={}
	bl=0
	vfm={}
	vfma={}
	while (i<len(tl)):
		if (tl[i][0]=="identifier"):
			si=i+0
			idl=[tl[i][1]]
			if (str(tl[i][1],"utf-8") in JS_RESERVED_IDENTIFIERS):
				if (tl[i][1] not in vfm):
					vfm[tl[i][1]]=1
				else:
					vfm[tl[i][1]]+=1
			else:
				if (si>0 and tl[si-1][0]=="keyword" and tl[si-1][1] in [b"let",b"const",b"var"]):
					vm[cl][tl[si][1]]=_gen_i(vm)
					idl[0]=vm[cl][tl[si][1]]
				elif (str(tl[si][1],"utf-8") not in JS_RESERVED_IDENTIFIERS and (si==0 or (tl[si-1][0]!="operator" or tl[si-1][1]!=b"."))):
					mv=_map_value(tl[si][1],vm)
					if (mv==None):
						print(f"Variable {tl[si][1]} is not mapped!")
					else:
						idl[0]=mv
			while (i+2<len(tl) and tl[i+1][0]=="operator" and tl[i+1][1]==b"." and tl[i+2][0]=="identifier"):
				idl+=[tl[i+2][1]]
				i+=2
			for k in idl[1:]:
				if (k not in vfma):
					vfma[k]=1
				else:
					vfma[k]+=1
			tl=tl[:si]+[("identifier",b".".join(idl))]+tl[i+1:]
			i=si
		elif (tl[i][0]=="keyword"):
			if (tl[i][1]==b"function"):
				si=i
				assert(i+5<len(tl))
				assert(tl[i+1][0]=="identifier")
				assert(str(tl[i+1][1],"utf-8") not in JS_RESERVED_IDENTIFIERS)
				nm=vm[cl][tl[i+1][1]]=_gen_i(vm[:cl+1])
				cl+=1
				vm+=[{}]
				assert(tl[i+2][0]=="operator")
				assert(tl[i+2][1]==b"(")
				i+=3
				al=[]
				while (True):
					if (len(al)>0 and tl[i][0]=="operator" and tl[i][1]==b","):
						i+=1
					if (tl[i][0]=="operator" and tl[i][1]==b")"):
						i+=1
						break
					va=False
					if (tl[i][0]=="operator" and tl[i][1]==b"..."):
						va=True
						i+=1
					assert(tl[i][0]=="identifier")
					vm[cl][tl[i][1]]=_gen_i(vm)
					al+=[(vm[cl][tl[i][1]],va)]
					i+=1
				assert(tl[i][0]=="operator")
				assert(tl[i][1]==b"{")
				ef+=[(bl,bl,si,i-si,nm,al)]
				if (bl not in efbl):
					efbl[bl]=[]
				efbl[bl]+=[len(ef)-1]
		elif (tl[i][0]=="operator"):
			s_ee=True
			ot=tl[i][1]
			if (tl[i][1]==b"{"):
				cl+=1
				vm+=[{}]
				ef+=[None]
				bl+=1
			elif (tl[i][1]==b"}"):
				cl-=1
				if (ef[-1]!=None):
					cbl,ocbl,si,fl,nm,al=ef[-1]
					efbl[ocbl].remove(len(ef)-1)
					j=1
					if (tl[si+fl+1][0]=="keyword" and tl[si+fl+1][1]==b"return"):
						j+=1
						cbl=ocbl
					ftl=([("keyword",b"let"),("identifier",nm),("operator",b"=")] if nm!=None else [])+([("operator",b"_=>")] if len(al)==0 else ([("identifier",al[0][0]),("operator",b"=>")] if len(al)==1 and al[0][1]==False else [("operator",b"(")]+_args(al)+[("operator",b")"),("operator",b"=>")]))
					tl=tl[:si]+ftl+([("operator",b"{")] if cbl==None else [])+tl[si+fl+j:i]+([("operator",b"}")] if cbl==None else [])+[("operator",b";")]+tl[i+1:]
					i+=-fl+len(ftl)-2+(2 if cbl==None else 0)-j+1
				vm=vm[:-1]
				ef=ef[:-1]
				bl-=1
				s_ee=False
			elif (tl[i][1]==b")"):
				bl-=1
				s_ee=False
			elif (tl[i][1]==b";"):
				if ((i>0 and tl[i-1][0]=="operator" and tl[i-1][1]==b"{") or (i+1<len(tl) and tl[i+1][0]=="operator" and tl[i+1][1] in [b";",b"}",b")"]) or i==len(tl)-1):
					tl=tl[:i]+tl[i+1:]
					i-=1
				else:
					s_ee=False
			elif (tl[i][1]==b"()=>"):
				tl[i]=("operator",b"_=>")
			elif (tl[i][1]==b"("):
				af=False
				if (i==0 or tl[i-1][0]!="identifier"):
					si=i+0
					al=[]
					i+=1
					cl+=1
					vm+=[{}]
					while (True):
						if (len(al)>0 and tl[i][0]=="operator" and tl[i][1]==b","):
							i+=1
						if (tl[i][0]=="operator" and tl[i][1]==b")"):
							i+=1
							break
						va=False
						if (tl[i][0]=="operator" and tl[i][1]==b"..."):
							va=True
							i+=1
						if (tl[i][0]!="identifier"):
							al=None
							break
						vm[cl][tl[i][1]]=_gen_i(vm)
						al+=[(vm[cl][tl[i][1]],va)]
						i+=1
					if (al==None or tl[i][0]!="operator" or tl[i][1]!=b"=>"):
						i=si
						cl-=1
						vm=vm[:-1]
					else:
						i+=1
						af=True
						if (tl[i][0]=="operator" and tl[i][1]==b"{"):
							ef+=[(bl,bl,si,i-si,None,al)]
							if (bl not in efbl):
								efbl[bl]=[]
							efbl[bl]+=[len(ef)-1]
						else:
							i-=1
							if (bl not in ee):
								ee[bl]=[]
							ee[bl]+=[(si,i-si,al)]
				if (af==False):
					bl+=1
					s_ee=False
			if (bl in efbl):
				for j in efbl[bl]:
					if (ef[j][0]==-1):
						ef[j]=(None,*ef[j][1:])
			if (s_ee==False):
				if (bl in ee):
					for k in ee[bl]:
						si,fl,al=k
						ftl=([("operator",b"_=>")] if len(al)==0 else ([("identifier",al[0][0]),("operator",b"=>")] if len(al)==1 and al[0][1]==False else [("operator",b"(")]+_args(al)+[("operator",b")"),("operator",b"=>")]))
						tl=tl[:si]+ftl+tl[si+fl+1:]
						i+=-fl+len(ftl)-1
						cl-=1
						vm=vm[:-1]
					del ee[bl]
				if (bl in efbl):
					for j in efbl[bl]:
						if (ef[j][0]==bl):
							ef[j]=(-1,*ef[j][1:])
		i+=1
	cvm={}
	sl=[]
	for k,v in vfm.items():
		mv=_gen_i([cvm],b=JS_CONST_LETTERS)
		if (len(mv)*(v+1)+len(k)+2<=len(k)*v):
			cvm[k]=mv
			if (len(sl)==0):
				sl=[("keyword",b"let")]
			else:
				sl+=[("operator",b",")]
			sl+=[("identifier",mv),("operator",b"="),("identifier",k)]
	cvma={}
	for k,v in vfma.items():
		mv=_gen_i([cvm,cvma],b=JS_CONST_LETTERS)
		if (len(mv)+len(k)+(len(mv)+2)*v+4<=(len(k)+1)*v):
			cvma[k]=mv
			if (len(sl)==0):
				sl=[("keyword",b"let")]
			else:
				sl+=[("operator",b",")]
			sl+=[("identifier",mv),("operator",b"="),("string",b"\""+k+b"\"")]
	if (len(sl)>0):
		tl=sl+[("operator",b";")]+tl
	o,_=_write(tl,cvm,cvma)
	print(f"Minified JS File '{fp}': {ofl} -> {len(o)} (-{round(10000-10000*len(o)/ofl)/100}%)")
	return o



def _copy(fp,f=lambda e,fp:e):
	with open(fp,"rb") as rf,open(f"{BASE}/{fp}","wb") as wf:
		wf.write(f(rf.read(),fp))



if (os.path.exists(BASE)==False):
	os.mkdir(BASE)
	cwd=os.getcwd()
	os.chdir(BASE)
	if (subprocess.run(["git","init"]).returncode!=0):
		os.chdir(cwd)
		quit()
	if (subprocess.run(["git","config","--global","user.email",f"\"{EMAIL}\""]).returncode!=0):
		os.chdir(cwd)
		quit()
	if (subprocess.run(["git","config","--global","user.name",f"\"{USER_NAME}\""]).returncode!=0):
		os.chdir(cwd)
		quit()
	if (subprocess.run(["heroku","git:remote","-a",f"{APP_NAME}"]).returncode!=0):
		os.chdir(cwd)
		quit()
	os.chdir(cwd)
for k in os.listdir(BASE):
	if (k==".git"):
		continue
	if (os.path.isdir(f"{BASE}\\{k}")==True):
		shutil.rmtree(f"{BASE}\\{k}")
	else:
		os.remove(f"{BASE}\\{k}")
os.mkdir(f"{BASE}/web")
os.mkdir(f"{BASE}/web/js")
os.mkdir(f"{BASE}/web/css")
os.mkdir(f"{BASE}/pages")
os.mkdir(f"{BASE}/server")
_copy("web/index.html")
_copy("web/not-found.html")
_copy("web/_template.html")
for fn in os.listdir("web/css"):
	_copy(f"web/css/{fn}",f=_minify_css)
for fn in os.listdir("web/js"):
	_copy(f"web/js/{fn}",f=_minify_js)
for fn in os.listdir("pages"):
	_copy(f"pages/{fn}")
for fn in os.listdir("server"):
	if (os.path.isfile(f"server/{fn}")==True):
		_copy(f"server/{fn}")
with open(f"{BASE}/runtime.txt","w") as f:
	f.write("python-3.9.0")
with open(f"{BASE}/requirements.txt","w") as f:
	f.write("\n")
with open(f"{BASE}/Procfile","w") as f:
	f.write("web: python server/main.py\n")
cwd=os.getcwd()
os.chdir(BASE)
if (subprocess.run(["git","add","."]).returncode!=0):
	os.chdir(cwd)
	quit()
if (subprocess.run(["git","commit","-am",f"\"Push {time.time()}\""]).returncode!=0):
	os.chdir(cwd)
	quit()
if (subprocess.run(["git","push","-f","heroku","master"]).returncode!=0):
	os.chdir(cwd)
	quit()
os.chdir(cwd)