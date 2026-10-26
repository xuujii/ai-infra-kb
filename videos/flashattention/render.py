"""Render a narrated FlashAttention lesson. No GPU or network is needed.
Dependencies: Pillow; imageio-ffmpeg (only supplies a local ffmpeg binary).
"""
from pathlib import Path
import bisect, json, math, subprocess, sys, wave
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(Path('D:/career/tmp/flash-video-tools')))
import imageio_ffmpeg

W, H, FPS = 1280, 720, 20
BG = '#0a1424'; PANEL = '#111f33'; LINE = '#293d55'
WHITE = '#eef5ff'; MUTED = '#a7b8cb'; TEAL = '#54e0c1'; ORANGE = '#ffb56b'; BLUE = '#72a9ff'
CHAPTERS = ['大仓库与小工作台', '原始 Attention 的数据流', '中间矩阵为什么昂贵', '第一招 · 分块', '第二招 · 在线 Softmax', '第三招 · 反向重计算', '适用范围与关键结论']
TITLES = ['少搬数据，为什么反而更快？', '先算分数，再算权重，最后汇总', '序列翻倍，中间表变成四倍', '一块算完，立刻用于更新输出', '分块之后，怎样得到同一个结果？', '需要概率块时，再算出来', '改变数据流，保留数学定义']
FONTS = Path('C:/Windows/Fonts')

@lru_cache(None)
def font(size, bold=False):
    return ImageFont.truetype(str(FONTS / ('msyhbd.ttc' if bold else 'msyh.ttc')), size)

def txt(d, pos, value, size=26, color=WHITE, bold=False):
    d.text(pos, str(value), font=font(size, bold), fill=color)

def center(d, box, value, size=26, color=WHITE, bold=False):
    x0,y0,x1,y1=box; f=font(size,bold)
    d.text(((x0+x1)/2,(y0+y1)/2),str(value),font=f,fill=color,anchor='mm')

def card(d, box, fill=PANEL, outline=LINE, radius=20):
    d.rounded_rectangle(box, radius, fill=fill, outline=outline, width=2)

def arrow(d, a, b, color=TEAL, width=4):
    d.line([a,b],fill=color,width=width)
    ang=math.atan2(b[1]-a[1],b[0]-a[0]); length=12
    d.polygon([b,(b[0]-length*math.cos(ang-.45),b[1]-length*math.sin(ang-.45)),(b[0]-length*math.cos(ang+.45),b[1]-length*math.sin(ang+.45))],fill=color)

def particles(d,a,b,t,color=TEAL,count=3):
    for i in range(count):
        p=(t*.32+i/count)%1
        x=a[0]+p*(b[0]-a[0]); y=a[1]+p*(b[1]-a[1])
        d.ellipse((x-5,y-5,x+5,y+5), fill=color)

def grid(d,x,y,size=150,n=8,active=None,color=BLUE):
    gap=3; cell=(size-(n-1)*gap)/n
    for r in range(n):
        for c in range(n):
            on=active is None or (r//2,c//2)==active
            d.rounded_rectangle((x+c*(cell+gap),y+r*(cell+gap),x+c*(cell+gap)+cell,y+r*(cell+gap)+cell),3,fill=color if on else '#22334b')

def wrap(d,value,size,width):
    lines=[]; line=''
    for c in value:
        if d.textlength(line+c,font=font(size))>width:
            lines.append(line); line=c
        else: line+=c
    if line: lines.append(line)
    return lines

def prepare():
    story=json.loads((ROOT/'story.json').read_text(encoding='utf-8'))
    timeline=[]; cursor=0; audio=[]; params=None
    for i, item in enumerate(story):
        with wave.open(str(ROOT/'audio'/f'{i:02}.wav'),'rb') as f:
            current=f.getparams(); data=f.readframes(f.getnframes())
        if params is None: params=current
        assert current[:3]==params[:3], 'All audio segments must use identical PCM formats.'
        lead=.35 if i==0 else .22
        tail=.45 if i<len(story)-1 else 1.8
        silence=lambda secs:b'\x00'*(int(secs*params.framerate)*params.nchannels*params.sampwidth)
        audio.extend([silence(lead),data,silence(tail)])
        length=len(data)/(params.framerate*params.nchannels*params.sampwidth)
        timeline.append({**item,'start':cursor,'speech_start':cursor+lead,'speech_end':cursor+lead+length,'end':cursor+lead+length+tail})
        cursor=timeline[-1]['end']
    with wave.open(str(ROOT/'narration.wav'),'wb') as out:
        out.setparams(params); out.writeframes(b''.join(audio))
    (ROOT/'timeline.json').write_text(json.dumps(timeline,ensure_ascii=False,indent=2),encoding='utf-8')
    return timeline,cursor

def draw_scene(d,scene,step,t):
    if scene==0:
        card(d,(70,205,510,502)); txt(d,(105,228),'HBM · 大容量显存',30,ORANGE,True)
        grid(d,116,302,164,color=ORANGE); txt(d,(303,324),'空间大',30); txt(d,(303,372),'搬运有成本',24,MUTED)
        card(d,(762,205,1210,502),outline=TEAL); txt(d,(798,228),'片上 SRAM · 小工作台',28,TEAL,True)
        grid(d,805,323,112,n=4,color=TEAL); txt(d,(946,336),'速度快',30); txt(d,(946,380),'容量有限',24,MUTED)
        arrow(d,(535,348),(736,348),ORANGE); particles(d,(535,348),(736,348),t,ORANGE)
        center(d,(516,374,753,433),'读写 / 搬运',24,MUTED)
    elif scene==1:
        cards=[(65,198,403,500),(472,198,810,500),(879,198,1217,500)]
        labels=[('① 打分','S = QK^T','分数表 S'),('② 归一化','P = softmax(S)','权重表 P'),('③ 加权汇总','O = PV','输出 O')]
        for i,(box,(name,formula,label)) in enumerate(zip(cards,labels)):
            card(d,box,outline=TEAL if i<=step else LINE)
            txt(d,(box[0]+25,218),name,27,TEAL if i<=step else MUTED,True)
            center(d,(box[0]+15,258,box[2]-15,310),formula,30)
            if i<2: grid(d,box[0]+102,327,134,color=ORANGE if step==2 else BLUE)
            else:
                for j in range(6):
                    bar=52+30*math.sin(j*1.3+.3)
                    d.rounded_rectangle((box[0]+64,330+j*21,box[0]+64+bar*2,345+j*21),4,fill=TEAL)
            center(d,(box[0],465,box[2],493),label,21,MUTED)
        for a,b in [((412,350),(458,350)),((820,350),(865,350))]:
            arrow(d,a,b,ORANGE); particles(d,a,b,t,ORANGE,1)
        if step==2: center(d,(80,509,1200,551),'完整中间表写入 HBM → 后续计算再读回',26,ORANGE,True)
        else: center(d,(80,509,1200,551),'示意省略 1/√d 缩放和掩码；实际计算仍需要它们',22,MUTED)
    elif scene==2:
        card(d,(70,202,610,520)); txt(d,(105,224),'每个头 · 每元素 2 字节',25,MUTED)
        grid(d,106,284,178,color=ORANGE); grid(d,320,284,178,color=ORANGE)
        center(d,(106,460,284,494),'S：32 MiB',24); center(d,(320,460,498,494),'P：32 MiB',24)
        card(d,(646,202,1210,520),outline=ORANGE)
        txt(d,(680,224),'N = 4096',34,ORANGE,True)
        txt(d,(680,282),'4096 × 4096',37,WHITE,True)
        txt(d,(680,342),'16,777,216 个元素 / 表',26,MUTED)
        txt(d,(680,398),'两张完整中间表 ≈ 64 MiB',29,ORANGE,True)
        if step==2:
            txt(d,(680,463),'N × 2  →  容量 × 4',29,TEAL,True)
        else: txt(d,(680,463),'这是容量示例，不是速度预测',24,MUTED)
    elif scene==3:
        card(d,(65,200,383,531)); txt(d,(91,220),'逻辑分数表 · 按块计算',23,BLUE,True)
        idx=int(t/2)%16; active=(idx//4,idx%4)
        grid(d,106,285,230,active=active,color=TEAL)
        card(d,(465,200,1000,531),outline=TEAL); txt(d,(493,221),'片上工作台：只保留当前小块',26,TEAL,True)
        for j,lab in enumerate(['Q 块','K 块','V 块']):
            box=(493+j*157,273,630+j*157,333); card(d,box,outline=BLUE); center(d,box,lab,24)
        box=(537,363,929,421); card(d,box,fill='#173c40',outline=TEAL)
        center(d,box,'分数小块 → 立即累积',26,TEAL,True)
        arrow(d,(695,340),(695,356)); arrow(d,(929,392),(1054,392)); particles(d,(929,392),(1054,392),t)
        box=(1058,272,1212,499); card(d,box,outline=TEAL)
        center(d,(1058,283,1212,343),'输出累积',23,TEAL,True)
        for k in range(5):
            v=45+12*math.sin(t+k)
            d.rounded_rectangle((1080,354+k*23,1080+v,368+k*23),4,fill=TEAL)
        arrow(d,(391,363),(451,363),BLUE); particles(d,(391,363),(451,363),t,BLUE,1)
        txt(d,(498,448),'用完即复用：不保存完整 S / P',24,WHITE)
        txt(d,(498,484),'下一块 K/V → 更新同一份输出累积',22,MUTED)
        if step==2: txt(d,(79,538),'Q/K/V 仍要读，最终输出仍要写；减少的是中间表 IO',23,MUTED)
    elif scene==4:
        txt(d,(80,186),'一个查询行 · V 简化为标量 · 指数值用于演示',23,MUTED)
        for i,(e,v) in enumerate(zip([1,2,4,3],[10,20,30,40])):
            box=(80+i*293,226,342+i*293,359)
            selected=(i<2 and step in [3,4]) or (i>=2 and step in [5,6]) or step==7
            card(d,box,outline=TEAL if selected else LINE)
            center(d,(box[0],237,box[2],297),f'exp(s) = {e}',29,TEAL if selected else WHITE,True)
            center(d,(box[0],305,box[2],350),f'V = {v}',25,MUTED)
        # Show the accumulation in the same place, so values changing is easy to follow.
        if step<=2:
            card(d,(80,391,1200,527),outline=BLUE)
            center(d,(80,397,1200,453),'完整计算：(1×10 + 2×20 + 4×30 + 3×40) / (1+2+4+3)',27)
            center(d,(80,459,1200,519),'290 / 10 = 29',36,TEAL,True)
            if step==0: center(d,(80,531,1200,563),'不能把各块单独归一化后直接平均',23,ORANGE)
        else:
            labels={3:('第一块：用尺度 2','[1, 2] / 2 = [0.5, 1]','U = 25','ℓ = 1.5'),4:('保留统计，暂不输出','U = 0.5×10 + 1×20 = 25','U = 25','ℓ = 1.5'),5:('新尺度 4：旧量一起 × 1/2','U: 25 → 12.5     ℓ: 1.5 → 0.75','U = 12.5','ℓ = 0.75'),6:('加入第二块：[4, 3] / 4','U = 12.5 + 1×30 + 0.75×40','U = 72.5','ℓ = 2.5'),7:('全部块处理完，再归一化','O = U / ℓ = 72.5 / 2.5 = 29','U = 72.5','ℓ = 2.5')}
            label,formula,u,l=labels[step]
            card(d,(80,388,829,527),outline=TEAL)
            txt(d,(105,404),label,28,TEAL,True); txt(d,(105,461),formula,26,WHITE)
            card(d,(852,388,1200,527),outline=TEAL)
            txt(d,(875,407),u,31,WHITE,True); txt(d,(875,464),l,31,WHITE,True)
            center(d,(80,531,1200,563),'U：未归一化的加权累积     ℓ：同一尺度下的指数和',22,MUTED)
    elif scene==5:
        card(d,(70,200,580,529)); txt(d,(103,220),'保存完整中间表的基线',27,ORANGE,True)
        grid(d,111,288,157,color=ORANGE)
        txt(d,(303,314),'前向保存 P',27); txt(d,(303,367),'反向读回 P',27)
        arrow(d,(110,476),(532,476),ORANGE); particles(d,(110,476),(532,476),t,ORANGE)
        card(d,(623,200,1210,529),outline=TEAL); txt(d,(657,220),'FlashAttention',31,TEAL,True)
        card(d,(654,282,1175,343),outline=BLUE); center(d,(654,282,1175,343),'保留 Q/K/V、O、行统计等',24)
        arrow(d,(911,351),(911,393)); particles(d,(911,351),(911,393),t)
        grid(d,662,410,78,n=4,color=TEAL)
        txt(d,(765,403),'重算当前 P 块 → 求梯度',25,TEAL,True)
        txt(d,(765,461),'多一点计算，少一些大表读写',23,MUTED)
        if step==1: center(d,(70,534,1210,565),'是否更快，取决于硬件、形状和基线实现',23,MUTED)
    else:
        for i,(name,desc,col) in enumerate([('分块','算一块，用一块',TEAL),('在线 Softmax','统一尺度，再归一化',BLUE),('反向重算','按需恢复概率块',ORANGE)]):
            box=(70+i*393,205,425+i*393,379); card(d,box,outline=col)
            txt(d,(box[0]+25,227),f'0{i+1}',24,col,True)
            center(d,(box[0],269,box[2],315),name,31,col,True)
            center(d,(box[0],325,box[2],367),desc,24)
        card(d,(70,400,1210,547),outline=TEAL)
        if step==0:
            txt(d,(100,420),'核心收益：减少 S / P 的中间显存读写',33,TEAL,True)
            txt(d,(100,482),'关注数据流，才能理解“多算一点也可能更快”',26,MUTED)
        elif step==1:
            txt(d,(100,420),'数学定义不变 · 浮点结果不保证逐位一致',29,TEAL,True)
            txt(d,(100,482),'Dense Attention 主要计算量仍是 O(N²)',29,MUTED)
        else:
            txt(d,(100,420),'重点场景：训练 / 长序列 Prefill',32,TEAL,True)
            txt(d,(100,482),'Decode 查询更短；实际收益需要测量',27,MUTED)

def frame(t,timeline,duration):
    starts=[x['start'] for x in timeline]
    index=max(0,min(len(timeline)-1,bisect.bisect_right(starts,t)-1))
    item=timeline[index]; scene=item['scene']; local=t-item['start']
    im=Image.new('RGB',(W,H),BG); d=ImageDraw.Draw(im)
    d.rectangle((0,0,11,H),fill=TEAL)
    txt(d,(60,31),'AI INFRA  /  微课 001',22,TEAL,True)
    txt(d,(60,76),TITLES[scene],43,WHITE,True)
    txt(d,(62,141),'FlashAttention  ·  '+CHAPTERS[scene],23,MUTED)
    txt(d,(1114,37),f'{scene+1:02} / 07',24,MUTED)
    draw_scene(d,scene,item['step'],local)
    d.rectangle((36,579,1244,680),fill='#13233a')
    lines=wrap(d,item['text'],27,1130)
    assert len(lines)<=2, 'Subtitle exceeds two lines'
    first_y=592 if len(lines)==2 else 612
    for i,line in enumerate(lines): center(d,(58,first_y+i*39,1222,first_y+37+i*39),line,27)
    d.rectangle((60,700,1220,705),fill=LINE)
    d.rectangle((60,700,60+1160*min(1,t/duration),705),fill=TEAL)
    return im

def stamp(t,sep=','):
    ms=round(t*1000); s,ms=divmod(ms,1000); m,s=divmod(s,60); h,m=divmod(m,60)
    return f'{h:02}:{m:02}:{s:02}{sep}{ms:03}'

def supporting_files(timeline,duration):
    srt=[]; vtt=['WEBVTT\n']
    for i,x in enumerate(timeline,1):
        srt.append(f'{i}\n{stamp(x["start"])} --> {stamp(x["end"])}\n{x["text"]}\n')
        vtt.append(f'{stamp(x["start"],".")} --> {stamp(x["end"],".")}\n{x["text"]}\n')
    (ROOT/'flashattention.srt').write_text('\n'.join(srt),encoding='utf-8-sig')
    (ROOT/'flashattention.vtt').write_text('\n'.join(vtt),encoding='utf-8')
    script=['# FlashAttention 短片讲解稿','',f'长度：{duration:.2f} 秒；中文合成旁白；中文字幕；1280×720 / {FPS} fps。','']
    for i,x in enumerate(timeline):
        script.extend([f'**{stamp(x["start"])} · {CHAPTERS[x["scene"]]}**',x['text'],''])
    script.extend(['技术依据：[FlashAttention 论文](https://arxiv.org/abs/2205.14135)。','在线 Softmax 的例子用于教学；指数值 [1,2,4,3] 对应分数 [ln1,ln2,ln4,ln3]。','容量示例为每个头、每元素 2 字节、完整保存 S/P 的教学基线；不代表所有后端的峰值内存。'])
    (ROOT/'讲解稿.md').write_text('\n'.join(script),encoding='utf-8')
    chapter_times=[next(x['start'] for x in timeline if x['scene']==i) for i in range(7)]
    buttons=''.join(f'<button data-time="{start:.3f}">{i+1:02} · {name}</button>' for i,(start,name) in enumerate(zip(chapter_times,CHAPTERS)))
    html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>FlashAttention · 动画微课</title><style>
    *{box-sizing:border-box}body{margin:0;background:#0a1424;color:#eef5ff;font-family:system-ui,"Microsoft YaHei",sans-serif}main{max-width:1120px;margin:auto;padding:28px 24px}a{color:#54e0c1}h1{font-size:clamp(24px,4vw,38px);margin:16px 0 10px}p{color:#a7b8cb;line-height:1.8}video{display:block;width:100%;border:1px solid #293d55;border-radius:16px;background:#000;margin:24px 0}nav{display:flex;flex-wrap:wrap;gap:10px}button{border:1px solid #293d55;background:#13233a;color:#eef5ff;padding:12px 15px;border-radius:9px;cursor:pointer;font:inherit}button:hover,button.active{border-color:#54e0c1;color:#54e0c1}.brand{color:#54e0c1;font-size:14px;letter-spacing:.1em}footer{margin-top:24px;border-top:1px solid #293d55;padding-top:12px}
    </style><main><div class="brand">AI INFRA / 微课 001</div><h1>FlashAttention：为什么少搬数据，反而更快？</h1><p>中文合成旁白 · 中文字幕 · 分块 / 在线 Softmax / 反向重计算</p><video id="lesson" controls playsinline preload="metadata" poster="poster.png"><source src="flashattention.mp4" type="video/mp4"><track kind="subtitles" src="flashattention.vtt" srclang="zh" label="中文（画面已含字幕）"></video><nav aria-label="视频章节">BUTTONS</nav><p>点击章节可跳到对应位置；播放器可调整播放速度。指数值的四个数用于教学，实际 Attention 使用向量和矩阵。</p><footer><a href="../../details/M007.html">阅读全文</a> · <a href="flashattention.mp4" download>下载 MP4</a> · <a href="讲解稿.md">讲解稿</a> · <a href="https://arxiv.org/abs/2205.14135">论文来源</a></footer></main><script>const v=document.querySelector('#lesson');const bs=[...document.querySelectorAll('button[data-time]')];bs.forEach(b=>b.onclick=()=>{v.currentTime=Number(b.dataset.time);v.play().catch(()=>{})});v.addEventListener('timeupdate',()=>{let i=bs.findLastIndex(b=>Number(b.dataset.time)<=v.currentTime);bs.forEach((b,j)=>b.classList.toggle('active',i===j))});</script></html>'''
    (ROOT/'index.html').write_text(html.replace('BUTTONS',buttons),encoding='utf-8')
    frame(0,timeline,duration).save(ROOT/'poster.png')
    for scene in range(7):
        candidates=[x for x in timeline if x['scene']==scene]
        sample=candidates[min(len(candidates)-1,len(candidates)//2)]
        frame(sample['start']+1,timeline,duration).save(ROOT/f'preview-{scene}.png')
    contact=Image.new('RGB',(1280,720),BG)
    for scene in range(7):
        im=Image.open(ROOT/f'preview-{scene}.png').resize((426,240))
        contact.paste(im,((scene%3)*426,(scene//3)*240))
    contact.save(ROOT/'contact-sheet.png')

def export(timeline,duration):
    ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
    command=[ffmpeg,'-y','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','pipe:0','-i',str(ROOT/'narration.wav'),'-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','veryfast','-crf','21','-pix_fmt','yuv420p','-c:a','aac','-b:a','112k','-movflags','+faststart','-shortest',str(ROOT/'flashattention.mp4')]
    count=math.ceil(duration*FPS)
    with (ROOT/'render.log').open('w',encoding='utf-8') as log:
        proc=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=log)
        try:
            for i in range(count):
                proc.stdin.write(frame(i/FPS,timeline,duration).tobytes())
                if i%(FPS*10)==0: print(f'Rendered {i/FPS:.0f}/{duration:.1f} seconds',flush=True)
        finally: proc.stdin.close()
        if proc.wait()!=0: raise RuntimeError('ffmpeg failed; see render.log')
    print(json.dumps({'duration':duration,'frames':count,'file':str(ROOT/'flashattention.mp4'),'bytes':(ROOT/'flashattention.mp4').stat().st_size}),flush=True)

if __name__=='__main__':
    timeline,duration=prepare(); supporting_files(timeline,duration)
    print(f'Prepared {len(timeline)} segments; duration {duration:.2f} seconds.',flush=True)
    if '--preview' not in sys.argv: export(timeline,duration)
