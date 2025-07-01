import math
import os
import random
import sys
import time
import pygame as pg


WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


def calc_orientation(org: pg.Rect, dst: pg.Rect) -> tuple[float, float]:
    """
    orgから見て，dstがどこにあるかを計算し，方向ベクトルをタプルで返す
    引数1 org：爆弾SurfaceのRect
    引数2 dst：こうかとんSurfaceのRect
    戻り値：orgから見たdstの方向ベクトルを表すタプル
    """
    x_diff, y_diff = dst.centerx-org.centerx, dst.centery-org.centery
    norm = math.sqrt(x_diff**2+y_diff**2)
    return x_diff/norm, y_diff/norm


class Bird(pg.sprite.Sprite):
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -1),
        pg.K_DOWN: (0, +1),
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (+1, 0),
    }

    def __init__(self, num: int, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 xy：こうかとん画像の位置座標タプル
        """
        super().__init__()
        img0 = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん
        self.imgs = {
            (+1, 0): img,  # 右
            (+1, -1): pg.transform.rotozoom(img, 45, 0.9),  # 右上
            (0, -1): pg.transform.rotozoom(img, 90, 0.9),  # 上
            (-1, -1): pg.transform.rotozoom(img0, -45, 0.9),  # 左上
            (-1, 0): img0,  # 左
            (-1, +1): pg.transform.rotozoom(img0, 45, 0.9),  # 左下
            (0, +1): pg.transform.rotozoom(img, -90, 0.9),  # 下
            (+1, +1): pg.transform.rotozoom(img, -45, 0.9),  # 右下
        }
        self.dire = (+1, 0)
        self.image = self.imgs[self.dire]
        self.rect = self.image.get_rect()
        self.rect.center = xy
        self.speed = 10
        self.state = "normal"  # 通常状態or無敵状態
        self.hyper_life = 0    # 無敵時間

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.image, self.rect)

    def reset_images(self):
        """
        無敵終了時に通常の画像（3.png）に戻す
        """
        try:
            img0 = pg.transform.rotozoom(pg.image.load(f"fig/3.png"), 0, 0.9)
            img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん
            self.imgs = {
                (+1, 0): img,  # 右
                (+1, -1): pg.transform.rotozoom(img, 45, 0.9),  # 右上
                (0, -1): pg.transform.rotozoom(img, 90, 0.9),  # 上
                (-1, -1): pg.transform.rotozoom(img0, -45, 0.9),  # 左上
                (-1, 0): img0,  # 左
                (-1, +1): pg.transform.rotozoom(img0, 45, 0.9),  # 左下
                (0, +1): pg.transform.rotozoom(img, -90, 0.9),  # 下
                (+1, +1): pg.transform.rotozoom(img, -45, 0.9),  # 右下
            }
            self.image = self.imgs[self.dire]
        except:
            # ファイルが見つからない場合は何もしない
            pass

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rect.move_ip(self.speed*sum_mv[0], self.speed*sum_mv[1])
        if check_bound(self.rect) != (True, True):
            self.rect.move_ip(-self.speed*sum_mv[0], -self.speed*sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)
            self.image = self.imgs[self.dire]
        
        # 無敵状態の処理
        if self.state == "hyper":
            # 画像を変換（エフェクト）
            self.image = pg.transform.laplacian(self.image)
            # 無敵時間を減算
            self.hyper_life -= 1
            if self.hyper_life < 0:
                self.state = "normal"
                # 無敵終了時に通常の画像に戻す
                self.reset_images()
        
        screen.blit(self.image, self.rect)


class Bomb(pg.sprite.Sprite):
    """
    爆弾に関するクラス
    """
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]

    def __init__(self, emy: "Enemy", bird: Bird):
        """
        爆弾円Surfaceを生成する
        引数1 emy：爆弾を投下する敵機
        引数2 bird：攻撃対象のこうかとん
        """
        super().__init__()
        rad = random.randint(10, 50)  # 爆弾円の半径：10以上50以下の乱数
        self.image = pg.Surface((2*rad, 2*rad))
        color = random.choice(__class__.colors)  # 爆弾円の色：クラス変数からランダム選択
        pg.draw.circle(self.image, color, (rad, rad), rad)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        # 爆弾を投下するemyから見た攻撃対象のbirdの方向を計算
        self.vx, self.vy = calc_orientation(emy.rect, bird.rect)  
        self.rect.centerx = emy.rect.centerx
        self.rect.centery = emy.rect.centery+emy.rect.height//2
        self.speed = 6
        self.state = "active"  # EMPで"inactive"に変更される


    def update(self):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class Beam(pg.sprite.Sprite):
    """
    ビームに関するクラス
    """
    def __init__(self, bird: Bird, angle0: float = 0):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん
        """
        super().__init__()
        self.vx, self.vy = bird.dire
        angle = math.degrees(math.atan2(-self.vy, self.vx)) + angle0
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/beam.png"), angle, 1.0)
        self.vx = math.cos(math.radians(angle))
        self.vy = -math.sin(math.radians(angle))
        self.rect = self.image.get_rect()
        self.rect.centery = bird.rect.centery+bird.rect.height*self.vy
        self.rect.centerx = bird.rect.centerx+bird.rect.width*self.vx
        self.speed = 10
        self.angle0 = angle0

    def update(self):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class NeoBeam():
    """
    複数ビームに関するクラス
    """
    def __init__(self, bird: Bird, num: int):
        self.bird = bird
        self.num = num
    
    def gen_beams(self) -> list[Beam, ]:
        """
        角度を変えたビームインスタンスの配列を返す
        """
        return [Beam(self.bird, i) for i in range(-180, +181, 361//(self.num-1))]

class Explosion(pg.sprite.Sprite):
    """
    爆発に関するクラス
    """
    def __init__(self, obj: "Bomb|Enemy", life: int):
        """
        爆弾が爆発するエフェクトを生成する
        引数1 obj：爆発するBombまたは敵機インスタンス
        引数2 life：爆発時間
        """
        super().__init__()
        img = pg.image.load(f"fig/explosion.gif")
        self.imgs = [img, pg.transform.flip(img, 1, 1)]
        self.image = self.imgs[0]
        self.rect = self.image.get_rect(center=obj.rect.center)
        self.life = life

    def update(self):
        """
        爆発時間を1減算した爆発経過時間_lifeに応じて爆発画像を切り替えることで
        爆発エフェクトを表現する
        """
        self.life -= 1
        self.image = self.imgs[self.life//10%2]
        if self.life < 0:
            self.kill()


class Enemy(pg.sprite.Sprite):
    """
    敵機に関するクラス
    """
    imgs = [pg.image.load(f"fig/alien{i}.png") for i in range(1, 4)]
    
    def __init__(self):
        super().__init__()
        self.image = pg.transform.rotozoom(random.choice(__class__.imgs), 0, 0.8)
        self.rect = self.image.get_rect()
        self.rect.center = random.randint(0, WIDTH), 0
        self.vx, self.vy = 0, +6
        self.bound = random.randint(50, HEIGHT//2)  # 停止位置
        self.state = "down"  # 降下状態or停止状態
        self.interval = random.randint(50, 300)  # 爆弾投下インターバル

    def update(self):
        """
        敵機を速度ベクトルself.vyに基づき移動（降下）させる
        ランダムに決めた停止位置_boundまで降下したら，_stateを停止状態に変更する
        引数 screen：画面Surface
        """
        if self.rect.centery > self.bound:
            self.vy = 0
            self.state = "stop"
        self.rect.move_ip(self.vx, self.vy)


class Score:
    """
    打ち落とした爆弾，敵機の数をスコアとして表示するクラス
    爆弾：1点
    敵機：10点
    """
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.value = 0
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, HEIGHT-50

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)

class Gravity(pg.sprite.Sprite):
    """
    画面全体を覆う重力場を発生させる
    """
    def __init__(self, life):
        super().__init__()
        self.life = life
        self.image = pg.Surface((WIDTH, HEIGHT))  
        pg.draw.rect(self.image, (0, 0, 0), (0, 0, WIDTH, HEIGHT)) 
        self.image.set_alpha(120)  
        self.rect = self.image.get_rect()

    def update(self):
        self.life -= 1
        if self.life < 0:
            self.kill()

class EMP(pg.sprite.Sprite):
    """
    電磁パルス（EMP）表示＋敵機＆爆弾の無効化
    """
    def __init__(self, emys: pg.sprite.Group, bombs: pg.sprite.Group, screen: pg.Surface):
        super().__init__()
        self.image = pg.Surface(screen.get_size()).convert_alpha()  # ←ここ重要：alpha対応
        self.image.fill((255, 255, 0, 128))  # RGBA指定で透明黄色
        self.rect = self.image.get_rect()
        self.life = 5  # 5フレーム ≒ 0.1秒に延ばして確実に見えるように

        # 敵機の無効化
        for emy in emys:
            emy.interval = float("inf")
            emy.image = pg.transform.laplacian(emy.image)

        # 爆弾の無効化
        for bomb in bombs:
            bomb.speed *= 0.5
            bomb.state = "inactive"

    def update(self):
        self.life -= 1
        if self.life < 0:
            self.kill()
      
      
class Shield(pg.sprite.Sprite):
    def __init__(self, bird: Bird, life: int):
        super().__init__()
        width = 20
        height = bird.rect.height * 2
        # 手順1: 空のSurface生成
        self.base_image = pg.Surface((width, height), pg.SRCALPHA)
        # 手順2: Surfaceにrectをdraw
        pg.draw.rect(self.base_image, (0, 0, 255), (0, 0, width, height))
        self.image = self.base_image
        self.rect = self.image.get_rect()
        self.life = life
        self.update(bird)  # 初期位置・角度反映

    def update(self, bird: Bird):
        # 手順3: こうかとんの向きを取得
        vx, vy = bird.dire
        # 手順4: 角度を求める
        angle = math.degrees(math.atan2(-vy, vx))
        # 手順5: Surfaceを回転
        self.image = pg.transform.rotozoom(self.base_image, angle, 1.0)
        self.rect = self.image.get_rect()
        # 手順6: こうかとんの中心から向きに応じて配置
        norm = math.hypot(vx, vy)
        if norm == 0:
            vx, vy = 1, 0
            norm = 1
        offset_dist = bird.rect.width  # こうかとん1体分
        ox = vx / norm * offset_dist
        oy = vy / norm * offset_dist
        self.rect.centerx = bird.rect.centerx + ox
        self.rect.centery = bird.rect.centery + oy
        self.life -= 1
        if self.life < 0:
            self.kill()

        
def main():
    pg.display.set_caption("真！こうかとん無双")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load(f"fig/pg_bg.jpg")
    score = Score()
    bird = Bird(3, (900, 400))
    
    emps = pg.sprite.Group()
    bombs = pg.sprite.Group()
    beams = pg.sprite.Group()
    exps = pg.sprite.Group()
    emys = pg.sprite.Group()
    gravity = pg.sprite.Group()
    shields = pg.sprite.Group()

    NUM_OF_BEAMS = 50 #1度に発射するビームの本数
    
    score.value = 10000
    tmr = 0
    clock = pg.time.Clock()
    while True:
        key_lst = pg.key.get_pressed()
        if key_lst[pg.K_e] and score.value >= 20:
            score.value -= 20
            emps.add(EMP(emys, bombs, screen))
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                beams.add(Beam(bird))
            if event.type == pg.KEYDOWN and event.key == pg.K_RETURN and score.value >= 200:
                g = Gravity(400)
                gravity.add(g)
                score.value -= 200
                
            if event.type == pg.KEYDOWN and event.key == pg.K_s:
                if score.value >= 50 and len(shields) == 0:
                    shields.add(Shield(bird, 400))
                    score.value -= 50

            if key_lst[pg.K_LSHIFT]:
                #複数ビーム
                if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                    beams.add(NeoBeam(bird, NUM_OF_BEAMS).gen_beams())
            
            # 無敵モード発動処理
            if event.type == pg.KEYDOWN and event.key == pg.K_RSHIFT:
                if score.value >= 100 and bird.state == "normal":
                    bird.state = "hyper"
                    bird.hyper_life = 500
                    score.value -= 100  # スコア消費

        #こうかとん高速化
        if key_lst[pg.K_LSHIFT]:
            bird.speed = 20
        else:
            bird.speed = 10
                    
        screen.blit(bg_img, [0, 0])

        if tmr%200 == 0:  # 200フレームに1回，敵機を出現させる
            emys.add(Enemy())

        for emy in emys:
            if emy.state == "stop" and tmr%emy.interval == 0:
                # 敵機が停止状態に入ったら，intervalに応じて爆弾投下
                bombs.add(Bomb(emy, bird))

        for emy in pg.sprite.groupcollide(emys, beams, True, True).keys():  # ビームと衝突した敵機リスト
            exps.add(Explosion(emy, 100))  # 爆発エフェクト
            score.value += 10  # 10点アップ
            bird.change_img(6, screen)  # こうかとん喜びエフェクト
        # ビームと爆弾の衝突判定
        for bomb in pg.sprite.groupcollide(bombs, beams, True, True).keys():
            exps.add(Explosion(bomb, 30))
            score.value += 1  # 爆弾を壊したら1点アップ

        # 防御壁と爆弾の衝突判定
        for shield in shields:
            for bomb in pg.sprite.spritecollide(shield, bombs, True):
                exps.add(Explosion(bomb, 30))

        for bomb in pg.sprite.spritecollide(bird, bombs, True):  # こうかとんと衝突した爆弾リスト
            if bird.state == "hyper":
                exps.add(Explosion(bomb, 50))
                score.value += 1

            elif bomb.state == "inactive":
                continue  # 無効化された爆弾は起爆しない
            else:
                bird.change_img(8, screen)  # こうかとん悲しみエフェクト
                score.update(screen)
                pg.display.update()
                time.sleep(2)
                return
        

        for g in gravity: # 爆弾と衝突判定
            for bomb in pg.sprite.spritecollide(g, bombs, False):
                exps.add(Explosion(bomb,50))
                bomb.kill()

            # 敵機と衝突判定
            for enemy in pg.sprite.spritecollide(g, emys, False):
                exps.add(Explosion(enemy,100))
                enemy.kill()
        
        gravity.update()
        gravity.draw(screen)
        shields.update(bird)
        shields.draw(screen)
        beams.update()
        beams.draw(screen)
        emys.update()
        emys.draw(screen)
        bombs.update()
        bombs.draw(screen)
        exps.update()
        exps.draw(screen)
        emps.update()
        emps.draw(screen) 
        bird.update(key_lst, screen)
        score.update(screen)
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()