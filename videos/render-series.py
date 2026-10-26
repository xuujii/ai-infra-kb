"""Three original narrated lessons; reuse the FlashAttention drawing primitives.
Run --preview to inspect frames, then run normally to export and register videos.
"""
from pathlib import Path
import bisect, importlib.util, json, math, subprocess, sys, wave
from functools import lru_cache
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('visuals',ROOT/'flashattention'/'render.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
W,H,FPS=v.W,v.H,v.FPS
BG,PANEL,LINE,WHITE,MUTED,TEAL,BLUE,ORANGE=v.BG,v.PANEL,v.LINE,v.WHITE,v.MUTED,v.TEAL,v.BLUE,v.ORANGE
COLORS={'A':TEAL,'B':BLUE,'C':ORANGE,'D':'#bb9bf7'}
font,card,txt,arrow,particles=v.font,v.card,v.txt,v.arrow,v.particles

@lru_cache(None)
def captions(value):
    d=ImageDraw.Draw(Image.new('RGB',(1,1)))
    lines=v.wrap(d,value,27,1130)
    if len(lines)<=1:return lines
    assert len(lines)==2,value
    candidates=[]
    for i in range(1,len(value)):
        if value[i] in '，。；：！？、':continue
        if value[i-1].isascii() and value[i].isascii() and value[i-1].isalnum() and value[i].isalnum():continue
        a=d.textlength(value[:i],font=font(27));b=d.textlength(value[i:],font=font(27))
        if max(a,b)<=1130:
            penalty=0 if value[i-1] in '，。；：！？' else 130
            candidates.append((abs(a-b)+penalty,i))
    if candidates:
        _,i=min(candidates);return [value[:i],value[i:]]
    return lines

def label(d,box,value,size=26,color=WHITE,bold=False):
    x0,y0,x1,y1=box
    while size>17 and d.textlength(str(value),font=font(size,bold))>x1-x0-12:size-=1
    v.center(d,box,value,size,color,bold)

def mini_block(d,box,name,col,used=16):
    card(d,box,outline=col,radius=9)
    x0,y0,x1,y1=box
    d.rounded_rectangle((x0+6,y1-13,x0+6+(x1-x0-12)*max(.001,used/16),y1-7),2,fill=col)
    label(d,(x0+2,y0,x1-2,y1-15),name,22,col,True)

def token_grid(d,x,y,count,n=64,color=TEAL):
    for i in range(n):
        row,col=divmod(i,16)
        d.rounded_rectangle((x+col*22,y+row*17,x+col*22+18,y+row*17+12),2,fill=color if i<count else '#26384f')

def kv_scene(d,scene,step,t):
    if scene==0:
        card(d,(70,206,1210,521));txt(d,(103,226),'Decode：当前查询读取历史与当前 K/V',29,TEAL,True)
        for i in range(5):
            box=(105+i*162,310,235+i*162,417)
            mini_block(d,box,f'位置 {i+1}',BLUE)
        new=(925,310,1171,417);mini_block(d,new,'加入当前 K/V',TEAL)
        arrow(d,(250,463),(1095,463),TEAL);particles(d,(250,463),(1095,463),t)
        txt(d,(106,480),'已有位置继续保留，后续生成还会读取',24,MUTED)
    elif scene==1:
        card(d,(70,202,610,526));txt(d,(102,219),'每请求最大预留 64 个位置',27,ORANGE,True)
        for i,(name,n) in enumerate([('A',17),('B',33),('C',8)]):
            y=285+i*76;txt(d,(100,y+10),f'{name} / {n}',23,COLORS[name],True);token_grid(d,225,y,n,color=COLORS[name])
        card(d,(644,202,1210,526),outline=ORANGE)
        txt(d,(679,233),'实际有效：17 + 33 + 8 = 58',29,WHITE,True)
        txt(d,(679,313),'分配：64 × 3 = 192',32,ORANGE,True)
        txt(d,(679,389),'空闲：192 − 58 = 134',30,ORANGE,True)
        txt(d,(679,464),'单位：token 槽位，不是字节',23,MUTED)
    elif scene==2 and step<2:
        card(d,(70,201,720,529));txt(d,(102,219),'块大小 = 16 · 只分配需要的块',27,TEAL,True)
        for i,(name,parts) in enumerate([('A',[16,1]),('B',[16,16,1]),('C',[8])]):
            y=281+i*77;txt(d,(103,y+16),name,28,COLORS[name],True)
            for j,n in enumerate(parts):mini_block(d,(160+j*169,y,310+j*169,y+61),f'{n} / 16',COLORS[name],n)
        card(d,(751,201,1210,529),outline=TEAL)
        txt(d,(785,231),'2 + 3 + 1 = 6 块',32,TEAL,True)
        txt(d,(785,310),'6 × 16 = 96 槽位',30,WHITE,True)
        txt(d,(785,388),'96 − 58 = 38 空闲',29,ORANGE,True)
        txt(d,(785,465),'有效数据没有减少',24,MUTED)
    elif scene==2:
        card(d,(70,199,561,513));txt(d,(98,220),'逻辑块 → 物理块',27,BLUE,True)
        for i,(name,ids) in enumerate([('A',[7,2]),('B',[4,9,1]),('C',[5])]):
            y=281+i*68;txt(d,(100,y+11),name,26,COLORS[name],True)
            for j,p in enumerate(ids):
                col=TEAL if step==3 and name=='A' and j==1 else COLORS[name]
                mini_block(d,(142+j*129,y,257+j*129,y+52),f'L{j} → P{p}',col)
        card(d,(636,199,1210,513));txt(d,(663,220),'显存物理块池 · 顺序可以打散',26,TEAL,True)
        owners={7:'A',2:'A',4:'B',9:'B',1:'B',5:'C'}
        for p in range(12):
            x=669+(p%4)*128;y=282+(p//4)*69;owner=owners.get(p)
            col=COLORS[owner] if owner else LINE
            mini_block(d,(x,y,x+110,y+53),f'P{p} · {owner or "空"}',col,16 if owner else 0)
            if step==3 and p==2:d.rounded_rectangle((x-4,y-4,x+114,y+57),12,outline=WHITE,width=3)
        arrow(d,(574,350),(623,350),TEAL);particles(d,(574,350),(623,350),t,TEAL,1)
        label(d,(75,520,1208,561),'第 17 个位置（索引 16）→ 逻辑块 1 → 物理块 2，偏移 0' if step==3 else '物理位置分散；token 的逻辑顺序与因果关系不变',24,TEAL)
    elif scene==3:
        card(d,(70,201,1210,529));txt(d,(103,220),'增长：已有块先用满，再申请下一块',27,TEAL,True)
        for i,(n,parts) in enumerate([(18,[16,2]),(33,[16,16,1])]):
            y=281+i*78;txt(d,(105,y+12),f'A / {n}',26,TEAL,True)
            for j,count in enumerate(parts):mini_block(d,(252+j*174,y,406+j*174,y+59),f'P{[7,2,8][j]} · {count}/16',TEAL,count)
        if step==0:
            txt(d,(827,312),'18：不需要新块',26,MUTED)
            txt(d,(827,387),'33：申请物理块 8',26,TEAL,True)
        else:
            mini_block(d,(834,287,1020,352),'P5 · C',ORANGE,8)
            arrow(d,(926,366),(926,409),TEAL);particles(d,(926,366),(926,409),t,TEAL,1)
            label(d,(804,413,1175,457),'C 结束 → P5 归还空闲池',26,TEAL)
        txt(d,(103,484),'回收前确认设备不再访问；然后允许新请求复用',24,MUTED)
    else:
        items=[('容量','减少最大长度预留',TEAL),('吞吐','给更多并发留空间',BLUE),('边界','每个 KV 元素并未压缩',ORANGE)]
        for i,(name,desc,col) in enumerate(items):
            box=(70+i*392,205,421+i*392,377);card(d,box,outline=col)
            label(d,(box[0],221,box[2],285),name,34,col,True)
            label(d,(box[0]+10,300,box[2]-10,355),desc,25,MUTED)
        card(d,(70,403,1210,538),outline=TEAL)
        label(d,(86,413,1194,468),'逻辑位置 → 查块表 → 物理块 → 读写 KV',31,TEAL,True)
        label(d,(86,478,1194,532),'系统和 Attention 内核共同配套；块内空闲和元数据仍存在',24,MUTED)

def batch_matrix(d,continuous,t):
    card(d,(70,206,1210,530));txt(d,(102,220),'连续批处理：每轮允许换人' if continuous else '固定批次：必须等 B 结束再整批替换',27,TEAL if continuous else ORANGE,True)
    rows=[['A','A','D','D','',''] if continuous else ['A','A','','','','D'],['B','B','B','B','B',''],['C','C','C','','','']]
    x0=268;unit=148
    for j in range(6):label(d,(x0+j*unit,259,x0+j*unit+132,291),f'轮 {j+1}',22,MUTED)
    for i,row in enumerate(rows):
        y=306+i*61;txt(d,(102,y+7),f'逻辑位置 {i+1}',22,MUTED)
        for j,name in enumerate(row):
            box=(x0+j*unit,y,x0+j*unit+132,y+49);col=COLORS.get(name,LINE)
            card(d,box,outline=col,fill=PANEL if name else '#172335',radius=8)
            label(d,box,name or '空',26,col if name else '#596a7e',True)
    cursor=x0+min(6,(t%13)/2.1)*unit
    if cursor<1170:d.line((cursor,298,cursor,487),fill='#a2bacd',width=2)
    txt(d,(102,495),'D 已完成 Prefill；各轮等时，D 后续两轮仅示意',22,MUTED)

def batching_scene(d,scene,step,t):
    if scene==0:
        card(d,(70,204,1210,526));txt(d,(102,221),'A / B / C：需要 2 / 5 / 3 轮 Decode',28,BLUE,True)
        for i,(name,n) in enumerate([('A',2),('B',5),('C',3)]):
            y=292+i*67;txt(d,(106,y+8),name,28,COLORS[name],True)
            for j in range(n):
                box=(179+j*146,y,310+j*146,y+46);card(d,box,outline=COLORS[name],radius=8);label(d,box,f'token {j+1}',22,COLORS[name])
                if j<n-1:arrow(d,(314+j*146,y+22),(320+j*146,y+22),COLORS[name],2)
        txt(d,(985,305),'短请求先结束',24,TEAL)
        txt(d,(985,366),'长请求继续生成',24,MUTED)
        txt(d,(102,490),'同一请求的下一步，仍依赖上一步生成的 token',23,MUTED)
    elif scene==1 or (scene==2 and step<2):
        batch_matrix(d,scene==2,t)
        if scene==2:label(d,(76,535,1205,564),'第 3 轮：D 接替 A，B / C 继续生成',23,TEAL,True)
        else:label(d,(76,535,1205,564),'第 3–5 轮留下空位；D 最早第 6 轮开始',23,ORANGE,True)
    elif scene==2:
        card(d,(70,205,1210,530));txt(d,(103,222),'按迭代管理活跃请求',29,TEAL,True)
        labels=['生成输出','判定结束','回收资源','选择下轮']
        active=int(t/2)%4
        for i,name in enumerate(labels):
            box=(105+i*276,311,339+i*276,398);card(d,box,outline=TEAL if active==i else LINE)
            label(d,box,name,29,TEAL if active==i else WHITE,True)
            if i<3:arrow(d,(345+i*276,355),(373+i*276,355),BLUE)
        d.line([(1120,409),(1120,472),(215,472)],fill=BLUE,width=3);arrow(d,(215,472),(215,413),BLUE)
        particles(d,(1040,472),(290,472),t,BLUE)
        label(d,(288,479,1108,520),'下一轮继续：保留活跃请求，也允许新成员加入',24,MUTED)
    elif scene==3:
        for i,(name,line1,line2,col) in enumerate([('输入计算','未完成 Prefill？','先处理提示词',ORANGE),('KV 容量','有空闲执行位置？','仍要有缓存空间',TEAL),('调度预算','本轮 token / 优先级','选择可以执行的工作',BLUE)]):
            box=(70+i*393,206,426+i*393,504);card(d,box,outline=col)
            label(d,(box[0],226,box[2],285),name,31,col,True)
            label(d,(box[0]+12,310,box[2]-12,363),line1,24,MUTED)
            label(d,(box[0]+12,383,box[2]-12,438),line2,25,WHITE,True)
        label(d,(70,515,1210,557),'Chunked Prefill / 分页 KV 可以配合使用；各自改变的机制不同',24,MUTED)
    else:
        for i,(name,desc,col) in enumerate([('总吞吐','每秒产出多少 token',TEAL),('TTFT','等多久看到第一个 token',BLUE),('TPOT','后续 token 的输出间隔',ORANGE)]):
            box=(70+i*393,206,426+i*393,396);card(d,box,outline=col)
            label(d,(box[0],227,box[2],300),name,35,col,True)
            label(d,(box[0]+12,319,box[2]-12,382),desc,24,MUTED)
        card(d,(70,421,1210,540),outline=TEAL)
        label(d,(83,431,1197,485),'利用请求之间的并行；保留请求内部的生成依赖',30,TEAL,True)
        label(d,(83,488,1197,535),'更大批次可能提高吞吐，也可能拉长输出间隔',24,MUTED)

def gantt(d,top,comm=1,overlap=False,scale=9,t=0):
    startx=228;width=918;unit=width/scale
    endprev=0;sends=[]
    for i in range(3):
        start=max((i+1)*2,endprev) if overlap else 6+i*comm
        sends.append((start,comm));endprev=start+comm
    for r,(name,intervals,col) in enumerate([('计算',[(i*2,2) for i in range(3)],BLUE),('归约',sends,ORANGE)]):
        y=top+r*52;txt(d,(107,y+5),name,23,col,True)
        d.line((startx,y+40,startx+width,y+40),fill=LINE,width=1)
        for i,(start,length) in enumerate(intervals):
            box=(startx+start*unit,y,startx+(start+length)*unit-3,y+37);card(d,box,outline=col,radius=5);label(d,box,f'{name}{i+1}',22,col,True)
    cursor=startx+(t%8)/8*scale*unit;d.line((cursor,top-4,cursor,top+95),fill='#7995ae',width=2)
    for n in range(scale+1):
        if scale>10 and n%2:continue
        label(d,(startx+n*unit-20,top+98,startx+n*unit+20,top+122),n,18,MUTED)
    return endprev

def overlap_scene(d,scene,step,t):
    if scene==0:
        card(d,(70,205,583,528));txt(d,(104,224),'本地反向：逐块产生梯度',27,BLUE,True)
        for i in range(3):
            box=(111+i*141,305,236+i*141,391);mini_block(d,box,f'梯度块 {i+1}',BLUE)
        txt(d,(103,459),'已就绪的梯度，有机会先归约',23,MUTED)
        card(d,(704,205,1210,528),outline=ORANGE);txt(d,(739,224),'跨设备：集合通信',27,ORANGE,True)
        for i in range(3):
            box=(745+i*147,305,867+i*147,391);card(d,box,outline=ORANGE);label(d,box,f'设备 {i+1}',23,ORANGE,True)
            if i<2:arrow(d,(868+i*147,349),(887+i*147,349),ORANGE)
        txt(d,(739,459),'汇总梯度后，再用于参数更新',23,MUTED)
        arrow(d,(601,350),(686,350),ORANGE);particles(d,(601,350),(686,350),t,ORANGE,1)
    elif scene==1:
        card(d,(70,205,1210,526));txt(d,(105,224),'计算每块 2 ms · 归约每块 1 ms',27,MUTED)
        gantt(d,300,t=t)
        label(d,(91,455,1188,515),'全部算完再归约：6 + 3 = 9 ms',34,ORANGE,True)
    elif scene==2:
        txt(d,(103,193),'串行',23,MUTED,True);gantt(d,227,t=t)
        txt(d,(103,362),'按桶就绪重叠',23,TEAL,True);gantt(d,395,overlap=True,t=t)
        label(d,(70,526,1210,565),'最后计算结束：6 ms     最后归约结束：7 ms     尾部仍有 1 ms',23,TEAL,True)
    elif scene==3 and step<2:
        card(d,(70,201,1210,532));txt(d,(105,219),'每块归约变成 4 ms，通信流排队',28,ORANGE,True)
        gantt(d,303,comm=4,overlap=True,scale=18,t=t)
        label(d,(86,459,1194,515),'串行：6 + 12 = 18 ms     重叠：14 ms',32,TEAL,True)
        label(d,(80,530,1200,561),'教学模型：双引擎，无启动与资源争用；时间轴单位为 ms',21,MUTED)
    elif scene==3:
        for i,(name,desc,col) in enumerate([('输入就绪','桶里的梯度齐了，才能归约',BLUE),('调用顺序','同组各卡保持一致顺序',ORANGE),('消费结果','参数更新等待所需归约',TEAL)]):
            box=(70+i*393,216,426+i*393,484);card(d,box,outline=col)
            label(d,(box[0],244,box[2],326),name,33,col,True)
            label(d,(box[0]+14,358,box[2]-14,436),desc,25,MUTED)
        label(d,(72,500,1208,556),'异步执行必须遵守依赖，不能把消费者任意提前',27,TEAL,True)
    else:
        card(d,(70,205,610,503),outline=BLUE);txt(d,(104,226),'运行时重叠',31,BLUE,True)
        label(d,(91,301,589,363),'独立计算 + 通信并行安排',27,WHITE,True)
        label(d,(91,398,589,456),'跨算子调度、分桶、参数预取',23,MUTED)
        card(d,(647,205,1210,503),outline=TEAL);txt(d,(681,226),'通算融合 · MC² 等',31,TEAL,True)
        label(d,(668,301,1189,363),'复合算子内部共同切块与编排',27,WHITE,True)
        label(d,(668,398,1189,456),'局部数据就绪，计算与通信流水',23,MUTED)
        label(d,(70,512,1210,558),'可配合使用；是否更快，要看完整关键路径与资源争用',24,MUTED)

def frame(lesson,t,timeline,duration):
    index=max(0,min(len(timeline)-1,bisect.bisect_right([x['start'] for x in timeline],t)-1))
    item=timeline[index];scene=item['scene'];local=t-item['start']
    im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im)
    d.rectangle((0,0,11,H),fill=TEAL)
    txt(d,(60,31),'AI INFRA  /  微课 '+lesson['number'],22,TEAL,True)
    label(d,(55,67,1210,132),lesson['titles'][scene],43,WHITE,True)
    txt(d,(62,141),lesson['id']+'  ·  '+lesson['chapters'][scene],23,MUTED)
    txt(d,(1114,37),f'{scene+1:02} / 05',24,MUTED)
    {'M016':kv_scene,'M021':batching_scene,'M026':overlap_scene}[lesson['id']](d,scene,item['step'],local)
    d.rectangle((36,579,1244,680),fill='#13233a');lines=captions(item['text'])
    assert len(lines)<=2,item['text']
    y=592 if len(lines)==2 else 612
    for i,line in enumerate(lines):label(d,(58,y+i*39,1222,y+37+i*39),line,27)
    d.rectangle((60,700,1220,705),fill=LINE);d.rectangle((60,700,60+1160*min(1,t/duration),705),fill=TEAL)
    return im

def prepare(lesson):
    out=ROOT/lesson['slug'];out.mkdir(exist_ok=True)
    (out/'story.json').write_text(json.dumps(lesson['story'],ensure_ascii=False,indent=2),encoding='utf-8')
    v.ROOT=out;timeline,duration=v.prepare()
    chapters=[{'name':name,'start':next(x['start'] for x in timeline if x['scene']==i)} for i,name in enumerate(lesson['chapters'])]
    srt=[];vtt=['WEBVTT\n'];script=['# '+lesson['title'],'',f'中文合成旁白 · 1280×720 · {FPS} fps · {duration:.2f} 秒','']
    for i,x in enumerate(timeline,1):
        srt.append(f'{i}\n{v.stamp(x["start"])} --> {v.stamp(x["end"])}\n{x["text"]}\n')
        vtt.append(f'{v.stamp(x["start"],".")} --> {v.stamp(x["end"],".")}\n{x["text"]}\n')
        script.extend([f'**{v.stamp(x["start"])} · {lesson["chapters"][x["scene"]]}**',x['text'],''])
    script.extend(['## 教学假设',lesson['assumptions'],'','## 原始资料',*[f'- [{s["title"]}]({s["url"]})' for s in lesson['sources']]])
    (out/'subtitles.srt').write_text('\n'.join(srt),encoding='utf-8-sig');(out/'subtitles.vtt').write_text('\n'.join(vtt),encoding='utf-8');(out/'讲解稿.md').write_text('\n'.join(script),encoding='utf-8')
    frame(lesson,0,timeline,duration).save(out/'poster.png')
    samples=[]
    for i in range(5):
        xs=[x for x in timeline if x['scene']==i];sample=xs[len(xs)//2]
        image=frame(lesson,sample['start']+1,timeline,duration);image.save(out/f'preview-{i}.png');samples.append(image)
    contact=Image.new('RGB',(1280,1080),BG)
    for i,im in enumerate(samples):contact.paste(im.resize((640,360)),((i%2)*640,(i//2)*360))
    contact.save(out/'contact-sheet.png')
    buttons=''.join(f'<button data-time="{c["start"]:.3f}">{i+1:02} · {c["name"]}</button>' for i,c in enumerate(chapters))
    html=f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{lesson['title']}</title><style>body{{margin:0;background:#0a1424;color:#eef5ff;font:15px/1.8 system-ui,"Microsoft YaHei"}}main{{max-width:1100px;margin:auto;padding:24px}}h1{{font-size:clamp(23px,4vw,34px)}}video{{width:100%;display:block;background:#000;border-radius:12px;margin:24px 0}}nav{{display:flex;gap:10px;flex-wrap:wrap}}button{{border:1px solid #293d55;background:#13233a;color:#eef5ff;border-radius:6px;padding:10px 12px;cursor:pointer}}a{{color:#54e0c1}}p{{color:#a7b8cb}}footer{{margin-top:25px}}</style><main><h1>{lesson['title']}</h1><p>中文合成旁白 · 画面含中文字幕 · 教学动画</p><video controls playsinline preload="metadata" poster="poster.png"><source src="video.mp4" type="video/mp4"><track kind="subtitles" src="subtitles.vtt" srclang="zh" label="中文"></video><nav>{buttons}</nav><footer><a href="../../details/{lesson['id']}.html">阅读全文</a> · <a href="讲解稿.md">讲解稿</a> · <a href="video.mp4" download>下载 MP4</a></footer></main><script>const v=document.querySelector('video');document.querySelectorAll('[data-time]').forEach(b=>b.onclick=()=>{{v.currentTime=Number(b.dataset.time);v.play().catch(()=>{{}})}});</script></html>'''
    (out/'index.html').write_text(html,encoding='utf-8')
    return out,timeline,duration,chapters

def export(lesson,out,timeline,duration):
    exe=v.imageio_ffmpeg.get_ffmpeg_exe()
    temporary=out/'video.rendering.mp4'
    cmd=[exe,'-y','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','pipe:0','-i',str(out/'narration.wav'),'-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','veryfast','-crf','21','-pix_fmt','yuv420p','-c:a','aac','-b:a','112k','-movflags','+faststart','-shortest',str(temporary)]
    with (out/'render.log').open('w',encoding='utf-8') as log:
        proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=log)
        try:
            for i in range(math.ceil(duration*FPS)):
                proc.stdin.write(frame(lesson,i/FPS,timeline,duration).tobytes())
                if i%(20*FPS)==0:print(f'{lesson["id"]}: {i/FPS:.0f}/{duration:.1f} seconds',flush=True)
        finally:proc.stdin.close()
        if proc.wait()!=0:raise RuntimeError('ffmpeg failed: '+str(out/'render.log'))
    temporary.replace(out/'video.mp4')

def register(lesson,duration,chapters):
    source=ROOT.parent/'videos.json';data=json.loads(source.read_text(encoding='utf-8'));prefix='videos/'+lesson['slug']+'/'
    data[lesson['id']]={'title':lesson['title'],'src':prefix+'video.mp4','poster':prefix+'poster.png','subtitles':prefix+'subtitles.vtt','timeline':prefix+'timeline.json','duration':f'{round(duration)//60} 分 {round(duration)%60} 秒','voice':'中文合成旁白','transcript':prefix+'讲解稿.md','chapters':chapters}
    source.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':
    lessons=json.loads((ROOT/'lessons.json').read_text(encoding='utf-8'))
    for lesson in lessons:
        if '--id' in sys.argv and lesson['id']!=sys.argv[sys.argv.index('--id')+1]:continue
        out,timeline,duration,chapters=prepare(lesson)
        print(f'{lesson["id"]}: prepared {duration:.2f} seconds',flush=True)
        if '--preview' not in sys.argv:
            export(lesson,out,timeline,duration);register(lesson,duration,chapters)
            print(json.dumps({'id':lesson['id'],'seconds':duration,'file':str(out/'video.mp4'),'bytes':(out/'video.mp4').stat().st_size}),flush=True)
