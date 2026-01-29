from PIL import Image, ImageDraw, ImageFont
import random
import string
from io import BytesIO
from flask import session

# 生成验证码图片
def generate_captcha():
    # 验证码字符集
    chars = string.ascii_letters + string.digits
    # 生成4位验证码
    captcha_text = ''.join(random.choice(chars) for _ in range(4))
    # 保存验证码到session
    session['captcha'] = captcha_text.lower()
    
    # 创建图片
    width, height = 120, 40
    image = Image.new('RGB', (width, height), (255, 255, 255))
    
    # 创建画笔
    draw = ImageDraw.Draw(image)
    
    # 生成随机颜色
    def random_color():
        return (random.randint(0, 120), random.randint(0, 120), random.randint(0, 120))
    
    # 绘制干扰线
    for _ in range(5):
        start = (random.randint(0, width), random.randint(0, height))
        end = (random.randint(0, width), random.randint(0, height))
        draw.line([start, end], fill=random_color(), width=1)
    
    # 绘制噪点
    for _ in range(50):
        draw.point((random.randint(0, width), random.randint(0, height)), fill=random_color())
    
    # 绘制验证码文本
    try:
        # 尝试使用系统字体
        font = ImageFont.truetype('arial.ttf', 28)
    except:
        # 如果系统没有arial字体，使用默认字体
        font = ImageFont.load_default()
    
    # 计算文本宽度
    text_width = draw.textlength(captcha_text, font=font)
    # 居中绘制文本
    x = (width - text_width) // 2
    y = (height - 30) // 2
    
    # 逐个字符绘制，增加随机性
    for i, char in enumerate(captcha_text):
        char_width = draw.textlength(char, font=font)
        draw.text((x, y), char, font=font, fill=random_color())
        x += char_width + 2
    
    # 保存到内存
    buffer = BytesIO()
    image.save(buffer, 'PNG')
    buffer.seek(0)
    
    return buffer

# 验证验证码
def verify_captcha(user_input):
    if 'captcha' not in session:
        return False
    
    stored_captcha = session['captcha']
    # 验证后删除验证码，防止重复使用
    del session['captcha']
    
    return user_input.lower() == stored_captcha

# 导出函数
__all__ = ['generate_captcha', 'verify_captcha']
