import streamlit as st
import random
import time
import os
import numpy as np
from PIL import Image, ImageDraw, Image as _PILImage
import io
import datetime
from fpdf import FPDF
import json
import math

# --- Bezpečné spouštění Pythonu pro IT ---
import ast
import contextlib
from io import StringIO

def is_code_safe(src: str) -> bool:
    try:
        tree = ast.parse(src, mode="exec")
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.With, ast.Try, ast.Raise)):
            return False
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"exec", "eval", "open", "__import__"}:
            return False
        if isinstance(node, ast.Attribute) and isinstance(node.attr, str) and node.attr.startswith("__"):
            return False
    return True

def run_user_code_capture_stdout(src: str):
    if not is_code_safe(src):
        return False, "Kód není povolen (import/exec/eval/with/try/open/__import__/__dunder__ zakázáno)."
    fake_out = StringIO()
    safe_builtins = {
        "print": print,
        "range": range,
        "len": len,
        "abs": abs,
        "round": round
    }
    env = {"__builtins__": safe_builtins}
    try:
        with contextlib.redirect_stdout(fake_out):
            exec(src, env, env)
    except Exception as e:
        return False, f"Chyba: {e}"
    return True, fake_out.getvalue().strip()

# -----------------------
# Pomocné utility (MA validace/parsování)
# -----------------------
def normalize_decimal(s: str):
    s = (s or "").strip().replace(" ", "").replace(",", ".")
    if s == "":
        raise ValueError("empty")
    return float(s)

def parse_fraction(s: str):
    if "/" not in s:
        raise ValueError("not a fraction")
    parts = s.replace(" ", "").split("/")
    if len(parts) != 2:
        raise ValueError("bad fraction")
    a = int(parts[0]); b = int(parts[1])
    if b == 0:
        raise ValueError("zero denom")
    return a, b

def gcd(a, b): return math.gcd(a, b)

def reduce_fraction(a, b):
    g = gcd(abs(a), abs(b))
    a //= g; b //= g
    if b < 0:
        a, b = -a, -b
    return a, b

def fraction_equal_reduced(user_str, target_str):
    ua, ub = parse_fraction(user_str)
    ra, rb = reduce_fraction(ua, ub)
    ta, tb = parse_fraction(target_str)
    ta, tb = reduce_fraction(ta, tb)
    # uživatel MUSÍ mít již zkráceno:
    return (ra == ta and rb == tb and (ua, ub) == (ra, rb))

def parse_div_remainder(s: str):
    ss = s.strip().lower().replace(" ", "")
    if "zb." not in ss:
        raise ValueError("missing 'zb.'")
    parts = ss.split("zb.")
    if len(parts) != 2:
        raise ValueError("bad format")
    q = int(parts[0]); r = int(parts[1])
    return q, r

def parse_ratio(s: str):
    ss = s.replace(" ", "")
    if ":" not in ss:
        raise ValueError("missing ':'")
    a, b = ss.split(":")
    a, b = int(a), int(b)
    return reduce_fraction(a, b)

def approx_equal(a: float, b: float, tol=1e-2):
    return abs(a - b) <= tol

# ---------------
# Pohádky (stručný obsah)
# ---------------
fairytales_data = {
    "Dráček z mechového lesa": {
        "text": "V Mechovém lese bydlel dráček Šimonek. S vílou Klárkou značili kroky kamínky a objevovali rytmus a melodii slov. V místech, kde mechy byly měkké jako polštáře a paprsky slunce tančily mezi větvemi, se scházeli. Dráček Šimonek nebyl žádný děsivý drak – byl celý zelený, měl kulaté bříško, třepotavá křidélka a smál se, až se mu od pusy místo ohně valily bubliny! Každý den létal nízko nad zemí a počítal, kolik hub vyrostlo, kolik ptáčků zpívá a kolik mravenců si staví cestu. Bavilo ho to – byl totiž moc zvědavý. Jednoho dne ale pršelo tak silně, že se všechny cestičky v lese roztekly. Dráček nevěděl, kudy domů. Sedl si pod kapradinu a smutně foukal bublinky. V tu chvíli kolem šla víla Klárka. „Šimonku, proč jsi smutný?“ zeptala se. „Ztratil jsem se! Neumím spočítat, kolik kroků vede k mojí jeskyni,“ povzdychl si dráček. „To nevadí,“ usmála se víla. „Spočítáme to spolu! Každých deset kroků označíme kamínkem.“ A tak šli. Po každých deseti krocích položili kamínek. Po dvaceti krocích – dva kamínky. Po třiceti – tři. A hádejte co? Když položili šestý kamínek, dráček vykřikl radostí: „To je moje jeskyně!“ Od té doby Šimonek vždy, když prší, pomáhá ostatním zvířátkům v lese najít cestu pomocí počítání kroků a kamínků. A víte co? Už se nikdy neztratil. Naučil se, že počítání může zachránit den.",
        "moral": "Naučme se prožívat – nejen čísla, ale i cestu k přátelství.",
        "obrazek_path": "dracek.png"
    },
    "O Šípkové Růžence": {
        "text": "Trny bludiště i vzory řeči: velké písmeno, tečka, slabiky. Matěj trpělivostí probudil království. Jak to bylo od začátku? Kdysi dávno se v království narodila malá princezna Růženka. Král s královnou uspořádali velkou oslavu a pozvali víly z celého světa. Každá víla přinesla princezně dar – krásu, zpěv, radost… Ale jedna víla nebyla pozvaná. A protože se urazila, přišla nepozvána a zvolala: „Až jí bude šestnáct, píchne se o trn a usne na sto let!“ Všichni se polekali. Jedna hodná víla ale řekla: „Nebude to navždy – až ji někdo s čistým srdcem najde, probudí se.“ Král dal spálit všechny trny v království. Ale jeden zůstal schovaný – v koutě staré věže. A tak když bylo Růžence právě šestnáct let, šla se projít po zámku. Objevila schody, po kterých nikdy nešla… a v prachu věže objevila starý kolovrátek. Píchla se – a v tu ránu usnula. Usnulo i celé království. Stromy narostly, trny prorostly zámek. Les spal. Sto let… Až jednoho dne přišel mladý kluk jménem Matěj. Byl zvědavý a odvážný. Když viděl, že trny tvoří bludiště, začal počítat, kudy se dostane dál. Počítal kroky, hledal vzory, skládal cesty. Až došel ke dveřím… Uvnitř uviděl dívku, která spala jako anděl. Matěj ji tiše oslovil: „Jsi Růženka? Já jsem Matěj. Přinesl jsem ti světlo dnešního dne.“ V tu chvíli se Růženka probudila. Les se prosvítil. Trny se proměnily v květy.         A co dál? Matěj s Růženkou se stali přáteli – a každý den počítali květiny, ptáky i roky, které už nespí.",
        "moral": "Trpělivost a pozorné čtení probouzí význam.",
        "obrazek_path": "ruzenka.png"
    },
    "Popelka": {
        "text": "Jednou byla dívka, která třídila fazole a slova; na plese vnímala hudbu i řeč – měkké a tvrdé souhlásky. V jedné daleké zemi žila dívka jménem Popelka. Její jméno vzniklo podle popela, který denně vymetala z krbu. I když žila v těžkých podmínkách – její nevlastní matka a dvě sestry jí stále poroučely – Popelka byla chytrá, trpělivá a měla dobré srdce. Když měla chvilku klidu, hrála si Popelka s kamínky a fazolemi. Nejenže z nich skládala obrazce, ale také počítala – sčítala je, řadila podle velikosti, třídila podle barvy. Matematika jí pomáhala zapomenout na starosti. Jednou večer přišel do vsi královský posel a rozhlásil: „Princ pořádá velký bál! Vybere si nevěstu. Každá dívka je zvána!“ Sestry se začaly chystat – počítaly šaty, boty a šperky: „Já mám 5 náušnic, ty máš 2... to je 7! Potřebujeme ještě 3 do deseti!“ Popelka tiše doufala, že půjde taky. Ale macecha jí jen řekla: „Ty nikam nejdeš, nemáš co na sebe – a nejdřív roztřiď 3 hrnce hrachu a čočky!“ Popelka si sedla a zoufala si – ale vtom se objevil bílý ptáček. „Pomohu ti. Ale musíš pomoci i ty mně – spočítej, kolik je 3x7.“ „To je dvacet jedna,“ řekla Popelka. Ptačí pomocníci zamávali křídly a všechna zrnka roztřídili. A vtom – zablesklo se. Na dvoře stála víla. „Zasloužíš si jít na ples. Pomohla jsi ostatním a umíš počítat!“ Mávla hůlkou – Popelka měla šaty poseté hvězdami, skleněné střevíčky a kočár z dýně. „Ale pamatuj – o půlnoci vše zmizí!“ Na plese Popelka okouzlila prince. Tancovali spolu a smáli se. Princ jí řekl: „Chci dívku, která má nejen krásné oči, ale i bystrý rozum. Položím ti hádanku: Když dnes máme 12 hostů, zítra přijde o 5 víc, kolik jich bude celkem?“ „Sedmnáct!“ usmála se Popelka. Princ byl ohromen. Ale hodiny odbily dvanáct, Popelka utekla… a ztratila jeden střevíček. Druhý den princ objížděl celé království a zkoušel skleněný střevíček dívce po dívce. V každém domě se zastavil, spočítal dívky a zapsal si, kolik pokusů už udělal. Až nakonec dorazil do posledního domu – kde našel tu pravou. Střevíček padl – a Popelka i princ věděli, že jejich životy se právě změnily.",
        "moral": "Krása bez rozumu nevydrží – ale rozum a laskavost září navždy. Ten, kdo počítá, třídí, učí se a pomáhá ostatním, nakonec najde cestu i ze smutku.",
        "obrazek_path": "popelka.png"
    },
    "Počítání s lesní vílou Klárkou": {
        "text": "V hlubokém zeleném lese, kde slunce jemně prosvítá mezi listy, žila malá víla jménem Klárka. Každé ráno si oblékla svou růžovou květinovou sukýnku a vyletěla ze své šiškové chaloupky. Víla Klárka měla důležitý úkol – počítat vše, co se v lese děje. Kolik květin rozkvetlo, kolik ptáčků se narodilo, kolik veverek si schovalo oříšky. Jenže jednoho dne se všechno zamotalo! 🌸 „Dnes mi to nějak nejde,“ povzdychla si Klárka. „Pořád ztrácím počet!“ Vtom přišel dráček Šimonek. „Já ti pomůžu,“ řekl. A tak začali spolu: 🐞 „Támhle jsou 3 berušky,“ řekla Klárka. 🐦 „A tam 2 sýkorky, to je dohromady…?“ „5!“ vykřikl Šimonek radostně.       Pak potkali 4 veverky a každá měla 2 oříšky. „Kolik oříšků dohromady?“ zeptala se víla. Šimonek chvilku počítal… „8 oříšků!“ Celý den tak spolu počítali. Nakonec Klárka řekla: „Díky, dráčku. Učila jsem les počítat, ale dneska mě to naučil les a Ty!“     A od té doby chodili lesem spolu – víla s kouzelnou hůlkou a dráček s bystrou hlavičkou.",
        "moral": "Počítání může být zábava – zvlášť, když na to nejsi sám!",
        "obrazek_path": "vila.png"
    },
    "Sněhurka a sedm trpaslíků": {
        "text": "Kdysi dávno žila krásná dívka jménem Sněhurka. Měla vlasy černé jako noc, pleť bílou jako sníh a srdce laskavé jako jarní slunce. Jednoho  dne musela utéct do lesa, protože zlá královna jí nepřála. Běhala mezi stromy, až narazila na malý domeček. Zaklepala, ale nikdo  neodpověděl. Opatrně vešla – uvnitř bylo sedm židliček, sedm hrníčků a sedm postýlek. Sněhurka byla unavená, a tak si na chvilku lehla. A co se nestalo? Domeček patřil sedmi trpaslíkům – každý měl jinou barvu čepičky a jméno podle své nálady: Červený: Veselík, Oranžový: Popleta, Žlutý: Sluníčko, Zelený: Moudřík, Modrý: Plačtík, Fialový: Chrápálek, Bílý: Počtář. Když Sněhurku našli, vůbec se nezlobili. Byli rádi, že s nimi zůstane – vařila jim, uklízela a učila počítat a poznávat barvy. Jednoho dne však přišla zlá královna v přestrojení a nabídla Sněhurce červené jablko. Ale nebylo obyčejné – bylo začarované! Sněhurka si kousla… a usnula. Trpaslíci byli smutní. Ale jednoho dne projížděl kolem lesem princ, který uslyšel, co se stalo. Položil jablko na váhu a zjistil, že červená půlka vážila víc než zelená – a byla to ta kouzelná! Když jablko rozlomili a zakouzlili kouzelnou formuli (kterou naučil Počtář), Sněhurka se probudila! A víte co? Všichni se radovali, tancovali podle barev duhy – a každý den počítali nové příběhy.",
        "moral": "Někdy i malý trpaslík nebo obyčejné číslo může změnit velký příběh.",
        "obrazek_path": "snehurka.png"
    },
    "Červená Karkulka": {
        "text": "Karkulka šla navštívit svou babičku a nesla jí jídlo. V lese potkala vlka, který ji přelstil a dostal se k babičce dřív. Naštěstí je obě zachránil statečný myslivec.",
        "moral": "Kdo je podmět, co je přísudek? Ve větě i v příběhu je důležité vědět, kdo co dělá a komu. Rozumět větám znamená rozumět příběhům.",
        "obrazek_path": "karkulka.png"
    },
    "O Zlatovlásce": {
        "text": "Kdysi dávno žila v zámku princezna jménem Zlatovláska. Měla vlasy jako slunce – zlaté, lesklé a dlouhé až po paty. Ale nebyla jen krásná, byla i moudrá a laskavá. Každý den se procházela v zahradě a povídala si s ptáčky, květinami i malými broučky. Jednoho dne se v království objevil mladý kuchař Jiřík. Pracoval na zámku a zaslechl, že princezna je zakletá: „Zlatovláska nemůže být šťastná, dokud někdo nesplní tři kouzelné úkoly,“ řekl starý zahradník. Jiřík se rozhodl, že jí pomůže. Nebál se ničeho – ani draka, ani hádanek. První úkol: „Přines z řeky perlu, kterou tam upustil král,“ řekla zlatá rybka. Jiřík skočil do vody, početl bubliny – bylo jich deset – a na dně našel perlu. Druhý úkol: „Rozlušti hádanku,“ řekla moudrá sova. „Když mám dvě křídla a neumím létat – co jsem?“ Jiřík přemýšlel… „Dveře!“ zvolal. A sova pokývala hlavou. Třetí úkol: „Najdi srdce princezny,“ řekla čarovná květina. Jiřík šel do zahrady, kam Zlatovláska ráda chodila, a posadil se. „Tady je její srdce. Miluje květiny, zvířata a svět,“ řekl tiše. V tu chvíli se zakletí zlomilo. Zlatovláska se usmála a její zlaté vlasy zazářily ještě víc než dřív. A jak to dopadlo? Jiřík zůstal na zámku, vařil tu nejlepší polévku na světě – a srdce Zlatovlásky bylo šťastné.",
        "moral": "Jiřík rozpozná přímou řeč, slovní druhy a stavbu věty. Moudrá řeč otevírá brány.",
        "obrazek_path": "zlatovlaska.png"
    },
    "Sněhová královna": {
        "text": "Byli jednou dva kamarádi – Gerda a Kaj. Každý den si hráli na zahradě, běhali, sbírali květiny a dívali se na hvězdy. Jednoho zimního dne ale přiletěla Sněhová královna. Byla krásná, ale studená jako led. Mráz jí létal kolem vlasů a vločky jí sedaly na ramena. Když Kaj koukal z okna, jedna vločka mu spadla přímo do oka a malý střep ledu mu vklouzl do srdce. Od té chvíle už nebyl stejný. Přestal se smát, začal být zlý a odešel s královnou do jejího ledového zámku na dalekém severu. Gerda byla smutná, ale nevzdala se. Vydala se Kaje hledat. Šla lesem, kolem řeky, potkala vrány, lišku, babičku s květinami, a dokonce i prince a princeznu. Všichni jí pomáhali. Nakonec došla až ke zmrzlému zámku, kde seděl Kaj – úplně ztichlý a bledý. Už si ani nepamatoval, kdo je. Gerda ho obejmula. A slza z jejího oka dopadla na jeho srdce. Led roztál. Kaj si vzpomněl! Drželi se za ruce, sníh kolem začal tát a celý ledový zámek se proměnil v jaro. Spolu se vrátili domů – šťastní, že se nikdy nevzdali.",
        "moral": "Přátelství a slova dokážou roztavit led.",
        "obrazek_path": "snehova_kralovna.png"
    },
    "Perníková chaloupka": {
        "text": "Kdysi dávno, v malé chalupě na okraji lesa, žil dřevorubec se svými dvěma dětmi – Jeníčkem a Mařenkou. Byli chudí, ale vždy si všechno dělili, i to nejmenší. Otec jim jednoho dne dal poslední, co měl: malé červené jablíčko. „Děti moje, podělte se,“ řekl. „Ať vám vydrží co nejdéle.“ Mařenka se usmála a řekla: „Půlka pro tebe, půlka pro mě.“ Jeníček přikývl, ale místo aby jablíčko rozkrojili, jen si z něj oba malinko kousli – a pak ho schovali. A co bylo zvláštní – jablko zůstalo celé. Nezdálo se, že by ubylo. „To je zvláštní,“ řekla Mařenka. „Asi ví, že se dělíme.“ Druhého dne je macecha zavedla hluboko do lesa. Děti si chtěly zapamatovat cestu zpět, ale déšť smyl stopy a ptáci sezobali drobky. Bloudili dlouho. Když měli hlad, vytáhli jablíčko. „Už nám moc nezbylo,“ řekl Jeníček. „Ale vždyť se na něj podívej – pořád je celé,“ zašeptala Mařenka. A opravdu – jablíčko zůstávalo kulaté, lesklé a šťavnaté, přestože se z něj občas kousli. Možná proto, že se nikdy nehádali, kdo má víc. Pak spatřili chaloupku – z perníku, cukroví a bonbonů. Voněla jako sen. Ale děti věděly, že něco, co je až příliš sladké, může být nebezpečné. Ulomili si jen kousek – a i ten si rozdělili. A jablíčko, které nosili s sebou, pořád zůstávalo v kapse – celé, teplé, jako by dýchalo. Vtom se otevřely dveře. Vyšla stará žena, vlídná na pohled. Pozvala je dovnitř, ale brzy zavřela Jeníčka do klece a Mařenku nutila vařit. Děti však neztratily naději – měly pořád své jablíčko, které si dávaly večer potají k nosu, aby si připomněly domov. Mařenka vymyslela plán. Když čarodějnice chtěla Jeníčka upéct, poprosila ji, ať jí ukáže, jak se leze do pece. Když tam vlezla, Mařenka dvířka zavřela. Děti se osvobodily a našly truhlu se zlaťáky. Ale největší poklad měly u sebe: jablíčko, které zůstávalo celé – protože se o něj vždy dělily. Na cestě domů potkávaly hladové zvířátko, unaveného poutníka – každému nabídly kousek. A jablko? Zůstávalo kulaté. Možná proto, že ten, kdo dává s láskou, nikdy nepřijde o to, co má.",
        "moral": "Jeníček a Mařenka dělí jablíčko i slova – slabiky, hlásky, významy. Poctivost a porozumění vedou domů.",
        "obrazek_path": "pernikova_chaloupka.png"
    },
    "O slepičce a kohoutkovi": {
        "text": "Byli jednou kohoutek Galois a slepička Poule. Celý den se spolu hrabali v prachu dvora a hledali dobrůtky. Byli nerozluční – vždy si dělili, co našli, a nikdy se nehádali. Jednoho dne, když už slunce zapadalo a země voněla večerem, našel kohoutek v hlíně zlatavé semínko – krásné, kulaté, lesklé, jaké ještě nikdy neviděli. „Jé, semínko!“ zakokrhal kohoutek. „Našel jsem ho první, je moje!“ Slepička ale sklopila hlavičku a tiše řekla: „Copak jsme se nedomluvili, že vše dělíme napůl?“ Kohoutek se zarazil. Dlouze se na semínko zadíval, pak na slepičku, a zase na semínko. „Ale když jsem ho našel první...“ zamumlal. A v tu chvíli se zlaté semínko zatřpytilo a začalo mizet. Kohoutek zůstal stát s otevřeným zobákem – semínko bylo pryč! V trávě zašuměl vánek a zněl jako hlas: „Co je sobecké, ztrácí se. Co je sdílené, roste.“ Kohoutek se podíval na slepičku. Zahanbeně sklonil hlavu. „Příště budeme dělit, ať najde kdo chce,“ řekl. A od té doby si vše, co našli, spravedlivě rozdělovali – i když to bylo jen jedno jediné semínko.",
        "moral": "Co je nalezeno pro sebe, bývá snadno ztraceno. Co je sdíleno, má sílu růst.",
        "obrazek_path": "slepicka.png"
    },
    "O jednorožci a dráčkovi": {
    "text": "V zemi za Duhovými horami žil bílý jednorožec jménem Lumin. Jeho roh zářil tak jasně, že dokázal prozářit i nejtemnější noc. Lumin miloval klid a ticho louky, kde rostly květiny všech barev, a každý den se procházel mezi nimi, aby nasbíral trochu radosti do svého kouzelného srdce. Jednoho dne uslyšel v dálce podivné šustění a šupinaté škrábání. Když se otočil, uviděl malého zeleného dráčka s kulatýma očima a křídly, která byla skoro větší než on sám. Dráček se jmenoval Fíglík – a byl to opravdový zvědavec. Uměl sice chrlit oheň, ale raději z něj dělal jen teplý vánek, aby nikomu neublížil. „Ahoj,“ zavolal Fíglík, „co tu děláš?“ „Sbírám světlo a radost do svého rohu,“ odpověděl Lumin a usmál se. „Světlo? To by se mi hodilo. V jeskyni, kde bydlím, je pořád tma.“ A tak se zrodil nápad – každý den spolu vyrazili na cestu: Lumin svým rohem osvětloval tmavé kouty lesa a Fíglík mu na oplátku pomáhal přeletět hluboké rokle, když mu nabídl křídla. Časem zjistili, že dohromady tvoří dokonalý tým – světlo a teplo, klid a hravost, zem a nebe. Jednoho večera se přihnala bouře. Lesem se prohnal vítr tak silný, že utrhl most přes řeku. Lumin by se sám přes vodu nedostal, ale Fíglík ho vzal na hřbet a přenesl ho do bezpečí. Vděčný jednorožec potom rozzářil celý břeh tak jasně, že ostatní zvířátka našla cestu domů. Od té doby byli Lumin a Fíglík nerozluční. A kdokoliv z kraje potřeboval pomoc, věděl, že když uvidí světlo rohu a zaslechne šustění malých dračích křídel, přichází dva nejlepší přátelé, kteří nikdy neodmítnou podat pomocnou ruku… nebo křídlo.", 
    "moral": "Skutečné přátelství vzniká tam, kde se lidé (nebo kouzelné bytosti) doplňují a pomáhají si. Každý má jiné schopnosti – a právě díky nim můžeme společně zvládnout to, co bychom sami nedokázali.",
    "obrazek_path":"jednorozec.png"
    },
}
# -----------------------
# Poznámky k učivu (ČJ)
# -----------------------
cjl_notes_by_level = {
    "1. třída": [
        "Hlásky, písmena, slabiky. Velké písmeno na začátku věty, tečka na konci.",
        "Doplňování písmen, počítání slabik (např.: slovo má 2 slabiky)."
    ],
    "2. třída": [
        "Měkké/tvrdé/obojetné souhlásky v kontextu slova.",
        "Vybrat správné i/y podle pravidel a významu věty."
    ],
    "3. třída": [
        "Vyjmenovaná slova (B, L, M, P, S, V, Z) a i/y v příbuzných slovech.",
        "Cvičení na doplňování i/y a rozlišení významů."
    ],
    "4. třída": [
        "Slovní druhy – základní orientace.",
        "Určování základních slovních druhů v krátkých větách."
    ],
    "5. třída": [
        "Větné členy (podmět, přísudek, předmět, příslovečná určení, přívlastek).",
        "Základní analýza jednoduchých vět."
    ],
    "6. třída": [
        "Mluvnické kategorie; shoda přísudku s podmětem; druhy vět; přímá řeč."
    ],
    "7. třída": [
        "Souvětí, spojky, druhy vedlejších vět (základní orientace)."
    ],
    "8. třída": [
        "Vedlejší věty, interpunkce v souvětí; slovní zásoba."
    ],
    "9. třída": [
        "Rekapitulace pravopisu; přímá řeč; literární minimum."
    ]
}

# -----------------------
# Poznámky k učivu (MA)
# -----------------------
math_notes_by_level = {
    "1. třída": [
        "Sčítání a odčítání do 20 (s i bez přechodu přes 10).",
        "Formát odpovědi: celé číslo (např. 14)."
    ],
    "2. třída": [
        "Sčítání a odčítání do 100. Malá násobilka 2–9.",
        "Formát odpovědi: celé číslo (např. 24, 7)."
    ],
    "3. třída": [
        "Sčítání/odčítání do 1000; dělení se zbytkem.",
        "Formát odpovědi (dělení se zbytkem): „podíl zb. zbytek“ (např. 5 zb. 2)."
    ],
    "4. třída": [
        "Násobení a dělení vícecifernými čísly; odhady a zaokrouhlování (na desítky/stovky).",
        "Formát odpovědi: celé číslo; u zaokrouhlení celé číslo (např. 350)."
    ],
    "5. třída": [
        "Desetinná čísla (±, ×/÷ jednociferným); zlomky (krácení, porovnání).",
        "Formát odpovědi: desetinná čísla na 2 desetinná místa (tečka i čárka); zlomky ve zkráceném tvaru „a/b“."
    ],
    "6. třída": [
        "Desetinná čísla (±); zlomky – sčítání/odčítání se stejným jmenovatelem; jednoduchá procenta (p% z N).",
        "Formát odpovědi: desetinná na 2 dp; zlomky ve zkráceném tvaru; procenta jako čisté číslo bez jednotky."
    ],
    "7. třída": [
        "Celá čísla (±, ×, ÷ jednociferným; i záporné výsledky); lineární rovnice ax+b=c; poměr a úměrnost.",
        "Formát odpovědi: číslo (může být záporné); poměr „a : b“ (zkráceně); u rovnice stačí hodnota x (např. 3)."
    ],
    "8. třída": [
        "Mocniny a odmocniny; Pythagorova věta; kruh (obvod/obsah, π≈3.14).",
        "Formát odpovědi: číslo; u kruhu na 2 desetinná místa."
    ],
    "9. třída": [
        "Rovnice (i se závorkami); x^2=a; statistika (průměr/medián); procenta/finanční (jednoduchý úrok, zpětné procento).",
        "Formát odpovědi: číslo; u x^2=a stačí jedna hodnota (např. -7 nebo 7); průměr na 2 dp; procenta/úrok čisté číslo."
    ]
}

# -----------------------
# Poznámky k učivu (IT) – hlavní téma NAHOŘE + vzorový kód
# -----------------------
it_notes_by_level = {
    "1. třída": [
        "Tisk textu a čísel pomocí příkazu print. (Navazuje na ČJ: čtení krátkých slov a vět; MA: malé počty.)",
        "Příklad – text:\n```python\nprint('Ahoj')\nprint(\"Drak\")\n```",
        "Příklad – čísla:\n```python\nprint(2+3)\nprint(3*4)\n```"
    ],
    "2. třída": [
        "Spojování textu a práce s délkou textu. (Navazuje na ČJ: slova a písmena.)",
        "Příklad – věta s mezerou:\n```python\nprint('Ahoj světe')\n```",
        "Příklad – délka slova:\n```python\nprint(len('pohádka'))  # vytiskne 7\n```",
        "Příklad – poslední písmeno:\n```python\ns = 'víla'\nprint(s[-1])  # vytiskne a\n```"
    ],
    "3. třída": [
        "Celé dělení // a zbytek %; poslední znak řetězce. (Navazuje na MA: dělení se zbytkem; ČJ: práce s písmeny.)",
        "Příklad – celočíselné dělení a zbytek:\n```python\nprint(10//3)  # 3\nprint(10%3)   # 1\n```",
        "Příklad – poslední písmeno:\n```python\ns = 'drak'\nprint(s[-1])  # k\n```"
    ],
    "4. třída": [
        "Podmínka (if/else), zaokrouhlení pomocí round, porovnání. (Navazuje na MA: zaokrouhlování, porovnávání.)",
        "Příklad – podmínka:\n```python\na = 5\nprint('ano' if a > 3 else 'ne')\n```",
        "Příklad – zaokrouhlení na 2 desetinná místa:\n```python\nprint(round(3.14159, 2))  # 3.14\n```",
        "Příklad – porovnání:\n```python\nprint(7 > 4)  # True\n```"
    ],
    "5. třída": [
        "Tisk a práce se seznamem: délka, poslední prvek, součet prvků. (Navazuje na MA: sčítání více čísel.)",
        "Příklad – délka seznamu:\n```python\nL = [1, 2, 3]\nprint(len(L))  # 3\n```",
        "Příklad – poslední prvek seznamu:\n```python\nL = [3, 6, 9]\nprint(L[-1])  # 9\n```",
        "Příklad – součet prvků seznamu cyklem:\n```python\nL = [4, 5, 9]\ns = 0\nfor x in L:\n    s += x\nprint(s)  # 18\n```"
    ],
    "6. třída": [
        "Desetinná čísla (2 desetinná místa) a procenta. (Navazuje na MA: procenta a desetinná čísla.)",
        "Příklad – 2 desetinná místa:\n```python\nprint(f\"{10/4:.2f}\")  # 2.50\n```",
        "Příklad – procenta:\n```python\ntotal = 200\np = 15\nprint(f\"{total*p/100:.2f}\")  # 30.00\n```"
    ],
    "7. třída": [
        "Celá čísla (i záporná), vlastní funkce, // a % se zápornými. (Navazuje na MA: celá čísla, jednoduché funkce v IT.)",
        "Příklad – sčítání se zápornými:\n```python\nprint(-3 + 5)  # 2\n```",
        "Příklad – funkce:\n```python\ndef dvojnasobek(x):\n    return x*2\nprint(dvojnasobek(6))  # 12\n```",
        "Příklad – dělení a zbytek se zápornými:\n```python\nprint(-11//4)\nprint(-11%4)\n```"
    ],
    "8. třída": [
        "Mocniny, odmocniny, Pythagoras, obvod kruhu. (Navazuje na MA: mocniny/odmocniny, geometrie.)",
        "Příklad – mocnina a odmocnina:\n```python\nprint(7**2)\nprint(49**0.5)\n```",
        "Příklad – Pythagoras (3,4,5):\n```python\na = 3; b = 4\nprint((a*a + b*b) ** 0.5)  # 5.0\n```",
        "Příklad – obvod kruhu r=5 (π≈3.14):\n```python\nr = 5\nprint(f\"{2*3.14*r:.2f}\")\n```"
    ],
    "9. třída": [
        "Průměr a medián seznamu, spojování slov do věty. (Navazuje na MA: statistika; ČJ: větná stavba.)",
        "Příklad – průměr (2 dp):\n```python\nL = [2, 4, 6]\nprint(f\"{sum(L)/len(L):.2f}\")  # 4.00\n```",
        "Příklad – medián u sudého počtu:\n```python\nL = [1, 4, 7, 8]\nm = (L[1] + L[2]) / 2\nprint(f\"{m:.2f}\")  # 5.50\n```",
        "Příklad – spojování slov do věty:\n```python\nslova = ['Učíme', 'se', 'Python']\nprint(' '.join(slova))\n```"
    ],
}

# -----------------------
# IT úkoly – 20/ročník, starter prázdný, hodnotí se stdout
# -----------------------
def build_it_tasks_by_level():
    tasks = {}
    # 1. třída
    t1 = []
    texts = ["Ahoj", "Drak", "Víla", "Python", "Les", "Popelka", "Šimonek", "Klárka", "Bublina", "Pohádka"]
    sums = [(2,3),(5,4),(7,2),(9,1),(6,3)]
    prods = [(2,5),(3,3),(4,2),(5,2),(6,2)]
    for s in texts:
        t1.append({"prompt": f"Vytiskni přesně text: {s}", "starter": "", "expected_stdout": s})
    for a,b in sums:
        t1.append({"prompt": f"Vytiskni výsledek {a}+{b}", "starter": "", "expected_stdout": str(a+b)})
    for a,b in prods:
        t1.append({"prompt": f"Vytiskni výsledek {a}*{b}", "starter": "", "expected_stdout": str(a*b)})
    tasks["1. třída"] = t1[:20]

    # 2. třída
    t2=[]
    pairs = [("Ahoj","světe"),("Dobrý","den"),("Víla","Klárka"),("Drak","Šimonek"),("Pohádky","baví")]
    words = ["les","strom","okno","kočka","drak","pohádka","víla","kámen"]
    for a,b in pairs:
        t2.append({"prompt": f"Vytiskni: {a} {b} (včetně mezery)", "starter": "", "expected_stdout": f"{a} {b}"})
    for w in words:
        t2.append({"prompt": f"Vytiskni délku slova '{w}'", "starter": "", "expected_stdout": str(len(w))})
    nums = [6,10,3,7,9,12,5,8]
    for x in nums:
        t2.append({"prompt": f"Do proměnné x ulož {x} a vytiskni x", "starter": "", "expected_stdout": str(x)})
    # doplňkové (poslední znak)
    t2.append({"prompt": "Vytiskni poslední písmeno slova 'víla'", "starter": "", "expected_stdout": "a"})
    t2.append({"prompt": "Vytiskni poslední písmeno slova 'drak'", "starter": "", "expected_stdout": "k"})
    tasks["2. třída"] = t2[:20]

    # 3. třída
    t3=[]
    divs=[(10,3),(12,5),(15,4),(20,6)]
    mods=[(10,3),(12,5),(15,4),(20,6)]
    strings=["víla","drak","les","pohádka","klíč","strom"]
    sums3=[(12,34),(7,15),(20,22),(9,11)]
    for a,b in divs:
        t3.append({"prompt": f"Vytiskni {a}//{b}", "starter":"", "expected_stdout": str(a//b)})
    for a,b in mods:
        t3.append({"prompt": f"Vytiskni {a}%{b}", "starter":"", "expected_stdout": str(a%b)})
    for s in strings:
        t3.append({"prompt": f"Vytiskni poslední písmeno slova '{s}'", "starter":"", "expected_stdout": s[-1]})
    for a,b in sums3:
        t3.append({"prompt": f"Vytiskni součet {a}+{b}", "starter":"", "expected_stdout": str(a+b)})
    tasks["3. třída"] = t3[:20]

    # 4. třída
    t4=[]
    for a in [5,2,7,0,10,3]:
        exp = "ano" if a>3 else "ne"
        t4.append({"prompt": f"Když a={a}, vytiskni 'ano', pokud a>3, jinak 'ne'.", "starter":"", "expected_stdout": exp})
    rounds=[3.14159,2.71828,1.995,2.345,7.005,5.555,12.349,0.845]
    for v in rounds:
        t4.append({"prompt": f"Zaokrouhli {v} na 2 desetinná místa a vytiskni", "starter":"", "expected_stdout": f"{round(v,2)}"})
    comps=[(7,4),(2,9),(5,5),(10,1),(3,3)]
    for a,b in comps:
        t4.append({"prompt": f"Vytiskni True/False: {a}>{b}", "starter":"", "expected_stdout": str(a>b)})
    tasks["4. třída"] = t4[:20]

    # 5. třída
    t5=[]
    lists=[[1,2,3],[10,20,30],[2,3,5],[4,5,9],[6,1,7],[8,0,2],[9,9,9],[3,6,9],[5,10,15],[7,8,9]]
    for L in lists[:7]:
        t5.append({"prompt": f"Vytiskni délku seznamu {L}", "starter":"", "expected_stdout": str(len(L))})
    for L in lists[7:10]:
        t5.append({"prompt": f"Vytiskni poslední prvek seznamu {L}", "starter":"", "expected_stdout": str(L[-1])})
    for L in lists[4:10]:
        t5.append({"prompt": f"Sečti prvky {L} cyklem for a vytiskni součet", "starter":"", "expected_stdout": str(sum(L))})
    tasks["5. třída"] = t5[:20]

    # 6. třída
    t6=[]
    decs=[(10,4),(7,2),(5,2),(9,4),(8,3)]
    for a,b in decs:
        t6.append({"prompt": f"Vytiskni {a}/{b} na 2 desetinná místa", "starter":"", "expected_stdout": f"{a/b:.2f}"})
    sums=[(3.5,2.25),(1.2,3.4),(5.55,2.45),(10.0,0.75),(2.345,2.005)]
    for a,b in sums:
        t6.append({"prompt": f"Vytiskni součet {a}+{b} na 2 dp", "starter":"", "expected_stdout": f"{(a+b):.2f}"})
    perc=[(200,15),(500,20),(250,12),(400,25),(800,5),(1000,30),(150,40),(90,50),(360,10),(720,15)]
    for total,p in perc[:10]:
        t6.append({"prompt": f"Vytiskni {p}% z {total} (na 2 dp)", "starter":"", "expected_stdout": f"{total*p/100:.2f}"})
    tasks["6. třída"] = t6[:20]

    # 7. třída
    t7=[]
    ints=[(-3,5),(7,-4),(-10,-2),(0,7),(-8,3),(5,0),(9,-9),(12,-5),(6,-11),(13,-7)]
    for a,b in ints:
        t7.append({"prompt": f"Vytiskni {a}+{b}", "starter":"", "expected_stdout": str(a+b)})
    t7.append({"prompt":"Definuj funkci dvojnasobek(x) a vytiskni dvojnasobek(6)","starter":"","expected_stdout":"12"})
    divmods=[(-10,3),(-11,4),(-7,5),(-20,6)]
    for a,b in divmods:
        t7.append({"prompt": f"Vytiskni {a}//{b}", "starter":"", "expected_stdout": str(a//b)})
        t7.append({"prompt": f"Vytiskni {a}%{b}", "starter":"", "expected_stdout": str(a%b)})
    tasks["7. třída"] = t7[:20]

    # 8. třída
    t8=[]
    powers=[(3,2),(4,2),(5,2),(2,3),(6,2),(7,2),(8,2),(9,2)]
    for n,e in powers:
        t8.append({"prompt": f"Vytiskni {n}**{e}", "starter":"", "expected_stdout": str(n**e)})
    roots=[9,16,25,36,49,64]
    for s in roots:
        t8.append({"prompt": f"Vytiskni druhou odmocninu z {s} (pomocí **0.5)", "starter":"", "expected_stdout": str(float(s**0.5))})
    pyth=[(3,4,5),(5,12,13),(6,8,10)]
    for a,b,c in pyth:
        t8.append({"prompt": f"Pro odvěsny {a} a {b} vytiskni přeponu (Pythagoras)", "starter":"", "expected_stdout": str(float(c))})
    circles=[3,4,5,7]
    for r in circles:
        t8.append({"prompt": f"Vytiskni obvod kruhu pro r={r} (π≈3.14, 2 dp)", "starter":"", "expected_stdout": f"{2*3.14*r:.2f}"})
    tasks["8. třída"] = t8[:20]

    # 9. třída
    t9=[]
    means=[[2,4,6],[1,2,3,4,5],[10,20,30],[5,5,5,5],[3,7,11]]
    for arr in means:
        t9.append({"prompt": f"Vytiskni průměr čísel {arr} (2 dp)", "starter":"", "expected_stdout": f"{sum(arr)/len(arr):.2f}"})
    med_pairs=[[1,4,7,8],[2,5,6,10],[3,3,7,9],[0,10,20,30]]
    for arr in med_pairs:
        med=(arr[1]+arr[2])/2
        t9.append({"prompt": f"Vytiskni medián čísel {arr} (2 dp)", "starter":"", "expected_stdout": f"{med:.2f}"})
    reverse=[(120,20),(150,50),(240,20),(330,10)]
    for new,p in reverse:
        t9.append({"prompt": f"Po zdražení o {p}% je cena {new}. Vytiskni původní (2 dp)", "starter":"", "expected_stdout": f"{(new/(1+p/100)):.2f}"})
    joins=[["Ahoj","jak","se","máš?"],["Dnes","je","pátek"],["Učíme","se","Python"],["Pohádky","nás","baví"]]
    for slova in joins:
        t9.append({"prompt": f"Sestav větu ze slov {slova} (mezera mezi slovy)", "starter":"", "expected_stdout": " ".join(slova)})
    tasks["9. třída"] = t9[:20]

    return tasks

it_tasks_by_level = build_it_tasks_by_level()

# -----------------------
# Generátor matematických úloh (MA)
# -----------------------
def generate_math_problem(level: str):
    lvl = (level or "").strip()

    if lvl == "1. třída":
        op = random.choice(["+", "-"])
        if op == "+":
            a = random.randint(0, 20)
            b = random.randint(0, 20 - a)
        else:
            a = random.randint(0, 20)
            b = random.randint(0, a)
        q = f"${a} {op} {b}$"
        ans = str(eval(f"{a}{op}{b}"))
        return q, ans, "int"

    elif lvl == "2. třída":
        t = random.choice(["add_sub", "mul"])
        if t == "add_sub":
            op = random.choice(["+", "-"])
            if op == "+":
                a = random.randint(0, 100)
                b = random.randint(0, 100 - a)
            else:
                a = random.randint(0, 100)
                b = random.randint(0, a)
            q = f"${a} {op} {b}$"
            ans = str(eval(f"{a}{op}{b}"))
            return q, ans, "int"
        else:
            a = random.randint(2, 9)
            b = random.randint(2, 9)
            q = f"${a} \\cdot {b}$"
            ans = str(a * b)
            return q, ans, "int"

    elif lvl == "3. třída":
        t = random.choice(["add_sub_1000", "div_remainder"])
        if t == "add_sub_1000":
            op = random.choice(["+", "-"])
            a = random.randint(0, 1000)
            b = random.randint(0, 1000)
            if op == "-":
                a, b = max(a, b), min(a, b)
            q = f"${a} {op} {b}$"
            ans = str(eval(f"{a}{op}{b}"))
            return q, ans, "int"
        else:
            d = random.randint(2, 9)
            qv = random.randint(2, 80)
            r = random.randint(0, d - 1)
            a = d * qv + r
            q = f"${a} \\div {d}$"
            ans = f"{qv} zb. {r}"
            return q, ans, "div_remainder"

    elif lvl == "4. třída":
        t = random.choice(["mul", "div", "round"])
        if t == "mul":
            a = random.randint(100, 999)
            b = random.randint(2, 20)
            q = f"${a} \\cdot {b}$"
            ans = str(a * b)
            return q, ans, "int"
        elif t == "div":
            b = random.randint(2, 20)
            qv = random.randint(50, 500)
            a = b * qv
            q = f"${a} \\div {b}$"
            ans = str(qv)
            return q, ans, "int"
        else:
            a = random.randint(100, 999)
            to = random.choice(["desítky", "stovky"])
            rounded = round(a / 10) * 10 if to == "desítky" else round(a / 100) * 100
            q = f"Zaokrouhli číslo {a} na {to}."
            ans = str(rounded)
            return q, ans, "int"

    elif lvl == "5. třída":
        t = random.choice(["dec_addsub", "dec_muldiv", "frac_simplify"])
        if t == "dec_addsub":
            a = round(random.uniform(1, 100), 2)
            b = round(random.uniform(0, 50), 2)
            op = random.choice(["+", "-"])
            if op == "-" and a < b:
                a, b = b, a
            q = f"${a} {op} {b}$"
            ans = f"{round(eval(f'{a}{op}{b}'), 2):.2f}"
            return q, ans, "decimal_2dp"
        elif t == "dec_muldiv":
            a = round(random.uniform(1, 100), 2)
            b = random.randint(2, 9)
            op = random.choice(["*", "/"])
            if op == "*":
                q = f"${a} \\cdot {b}$"
                ans = f"{round(a * b, 2):.2f}"
            else:
                q = f"${a} \\div {b}$"
                ans = f"{round(a / b, 2):.2f}"
            return q, ans, "decimal_2dp"
        else:
            num = random.randint(2, 18)
            den = random.randint(num + 1, 24)
            if math.gcd(num, den) == 1:
                den *= 2
            rn, rd = reduce_fraction(num, den)
            q = f"Zkrať zlomek $\\frac{{{num}}}{{{den}}}$ na základní tvar. (Zapiš jako čitatel/jmenovatel.)"
            ans = f"{rn}/{rd}"
            return q, ans, "fraction_reduced"

    elif lvl == "6. třída":
        t = random.choice(["dec_addsub", "frac_addsub_same", "percent_basic"])
        if t == "dec_addsub":
            a = round(random.uniform(1, 200), 2)
            b = round(random.uniform(1, 200), 2)
            op = random.choice(["+", "-"])
            if op == "-" and a < b:
                a, b = b, a
            q = f"${a} {op} {b}$"
            ans = f"{round(eval(f'{a}{op}{b}'), 2):.2f}"
            return q, ans, "decimal_2dp"
        elif t == "frac_addsub_same":
            den = random.randint(2, 12)
            a = random.randint(1, den - 1)
            b = random.randint(1, den - 1)
            if random.random() < 0.5:
                q = f"Sčítej: $\\frac{{{a}}}{{{den}}} + \\frac{{{b}}}{{{den}}}$ a zkrať."
                num = a + b
            else:
                big, small = max(a, b), min(a, b)
                q = f"Odčítej: $\\frac{{{big}}}{{{den}}} - \\frac{{{small}}}{{{den}}}$ a zkrať."
                num = big - small
            if num == 0:
                ans = "0/1"
            else:
                rn, rd = reduce_fraction(num, den)
                ans = f"{rn}/{rd}"
            return q, ans, "fraction_reduced"
        else:
            total = random.choice([100, 200, 250, 400, 500, 800, 1000])
            p = random.choice([5, 10, 12, 15, 20, 25, 30, 40, 50])
            q = f"Kolik je {p}% z {total}?"
            ans = f"{round(total * p / 100, 2):.2f}"
            return q, ans, "decimal_2dp_number_only"

    elif lvl == "7. třída":
        t = random.choice(["integers", "linear", "ratio", "proportion"])
        if t == "integers":
            a = random.randint(-50, 50)
            b = random.randint(-50, 50)
            op = random.choice(["+", "-"])
            q = f"${a} {op} {b}$"
            ans = str(eval(f"{a}{op}{b}"))
            return q, ans, "int"
        elif t == "linear":
            a = random.randint(2, 9)
            x_val = random.randint(-10, 10)
            b = random.randint(-10, 10)
            c = a * x_val + b
            q = f"Vyřeš rovnici: ${a}x + ({b}) = {c}$, najdi $x$."
            ans = str(x_val)
            return q, ans, "int"
        elif t == "ratio":
            a = random.randint(2, 50)
            b = random.randint(2, 50)
            ra, rb = reduce_fraction(a, b)
            q = f"Zkrať poměr {a} : {b}."
            ans = f"{ra} : {rb}"
            return q, ans, "ratio"
        else:
            a = random.randint(2, 12)
            b = random.randint(2, 12)
            x = random.randint(2, 12)
            d = a * x / b
            q = f"Vyřeš úměru: $\\frac{{{a}}}{{{b}}} = \\frac{{{x}}}{{?}}$"
            ans = f"{d:.2f}"
            return q, ans, "decimal_2dp"

    elif lvl == "8. třída":
        t = random.choice(["power", "root", "pythag", "circle"])
        if t == "power":
            n = random.randint(2, 10)
            e = random.choice([2, 3])
            q = f"${n}^{e}$"
            ans = str(n ** e)
            return q, ans, "int"
        elif t == "root":
            n = random.randint(2, 15)
            q = f"$\\sqrt{{{n*n}}}$"
            ans = str(n)
            return q, ans, "int"
        elif t == "pythag":
            triples = [(3, 4, 5), (5, 12, 13), (6, 8, 10)]
            a, b, c = random.choice(triples)
            side = random.choice(["c", "a", "b"])
            if side == "c":
                q = f"Trojúhelník má odvěsny a={a}, b={b}. Vypočítej přeponu c."
                ans = str(c)
            elif side == "a":
                q = f"Trojúhelník má přeponu c={c} a odvěsnu b={b}. Vypočítej odvěsnu a."
                ans = str(a)
            else:
                q = f"Trojúhelník má přeponu c={c} a odvěsnu a={a}. Vypočítej odvěsnu b."
                ans = str(b)
            return q, ans, "int"
        else:
            r = random.randint(3, 15)
            which = random.choice(["circumference", "area"])
            if which == "circumference":
                q = f"Vypočítej obvod kruhu s poloměrem r={r}. Použij $\\pi \\approx 3.14$ a 2 dp."
                ans = f"{round(2 * 3.14 * r, 2):.2f}"
            else:
                q = f"Vypočítej obsah kruhu s poloměrem r={r}. Použij $\\pi \\approx 3.14$ a 2 dp."
                ans = f"{round(3.14 * r * r, 2):.2f}"
            return q, ans, "decimal_2dp"

    elif lvl == "9. třída":
        t = random.choice(["linear_paren", "quadratic_simple", "statistics", "percent_reverse", "financial"])
        if t == "linear_paren":
            a = random.randint(2, 5)
            x_val = random.randint(-10, 10)
            b = random.randint(-5, 5)
            c = a * (x_val + b)
            q = f"Vyřeš rovnici: ${a}(x + {b}) = {c}$, najdi $x$."
            ans = str(x_val)
            return q, ans, "int"
        elif t == "quadratic_simple":
            squares = [4, 9, 16, 25, 36, 49, 64, 81, 100, 121, 144, 196]
            A = random.choice(squares)
            r = int(math.sqrt(A))
            q = f"Vyřeš rovnici: $x^2 = {A}$. (Stačí zadat jednu správnou hodnotu.)"
            return q, (str(r), str(-r)), "quadratic_one_of_two"
        elif t == "statistics":
            nums = sorted([random.randint(1, 40) for _ in range(random.randint(5, 7))])
            if random.random() < 0.5:
                q = "Vypočítej průměr čísel: " + ", ".join(map(str, nums)) + " (na 2 desetinná místa)."
                ans = f"{round(sum(nums) / len(nums), 2):.2f}"
                return q, ans, "decimal_2dp"
            else:
                n = len(nums)
                med = nums[n // 2] if n % 2 == 1 else (nums[n // 2 - 1] + nums[n // 2]) / 2
                q = "Urči medián čísel: " + ", ".join(map(str, nums)) + "."
                ans = f"{med:.2f}" if isinstance(med, float) else str(med)
                return q, ans, "decimal_or_int"
        elif t == "percent_reverse":
            p = random.choice([10, 15, 20, 25, 30, 40, 50])
            T = random.choice([110, 150, 200, 250, 300, 400, 500, 800, 1000])
            q = f"Po zdražení o {p}% stojí zboží {T} Kč. Kolik stálo původně? (na 2 dp)"
            ans = f"{round(T / (1 + p / 100), 2):.2f}"
            return q, ans, "decimal_2dp"
        else:
            principal = random.randint(1000, 20000)
            rate = random.choice([1, 1.5, 2, 2.5, 3, 4, 5])
            years = random.randint(1, 5)
            q = f"Jaký úrok získáš z {principal} Kč při roční sazbě {rate}% za {years} roky? (čisté číslo, 2 dp)"
            ans = f"{round(principal * (rate / 100) * years, 2):.2f}"
            return q, ans, "decimal_2dp_number_only"

    a = random.randint(1, 50)
    b = random.randint(1, 50)
    q = f"${a} + {b}$"
    ans = str(a + b)
    return q, ans, "int"

# -----------------------
# Streamlit UI
# -----------------------
st.set_page_config(page_title="Pohádky: MA / ČJ / IT (Python)", layout="wide")
st.title("🌟 Pohádky s matematikou, češtinou a informatikou (Python)")

# Session state init
defaults = dict(
    game_started=False, tasks_solved_for_reveal=0, score=0, best_score=0,
    best_time=float('inf'), start_time=None, end_time=None, current_task=None,
    last_selected_fairytale=None, last_selected_class=None, last_selected_subject=None,
    revealed_tiles=[False]*20, tile_coords=[], feedback_message="", feedback_type="",
    final_report=None, history=[], show_full_fairytale=False, achievement_date=None,
    diploma_image_path=None, _cjl_index=0, _it_index=0, _it_last_output="",
    _it_last_eval="", current_cjl_task=None
)
for k,v in defaults.items():
    if k not in st.session_state: st.session_state[k]=v

TASKS_TO_REVEAL = 20
class_to_db_level = {f"{i}. třída": f"{i}. třída" for i in range(1,10)}

# Sidebar
st.sidebar.title("📚 Výběr pohádky")
fairytale_titles = list(fairytales_data.keys())
vyber = st.sidebar.selectbox("Vyberte pohádku", fairytale_titles)
tridy = [f"{i}. třída" for i in range(1,10)]
vyber_tridy = st.sidebar.selectbox("Vyberte úroveň", tridy)
st.sidebar.markdown("---")
subject = st.sidebar.radio("Předmět", options=["MA","ČJ","IT"], index=0, horizontal=True)

# ČJ – načtení statických úloh
cjl_tasks_by_level = {}
for pth in ["cjl_tasks.json", "/mnt/data/cjl_tasks.json"]:
    if os.path.exists(pth):
        with open(pth, "r", encoding="utf-8") as f:
            cjl_tasks_by_level = json.load(f)
        break

def get_tile_coordinates(image_path, rows, cols):
    if not image_path or not os.path.exists(image_path): return []
    img = _PILImage.open(image_path); w,h = img.size; tw,th = w//cols, h//rows
    coords=[]
    for r in range(rows):
        for c in range(cols):
            coords.append((c*tw, r*th, (c+1)*tw, (r+1)*th))
    return coords

def generate_diploma_pdf(username, score, time_s, fairytale_title,
                         achievement_date, level, subject_display,
                         topic_line, image_path,
                         crop_mode="auto"):
    pdf = FPDF(orientation='L', unit='mm', format='A4'); pdf.add_page()
    pw, ph = pdf.w, pdf.h
    try:
        pdf.add_font("DejaVuSans","", "DejaVuSansCondensed.ttf", uni=True)
        pdf.add_font("DejaVuSans","B","DejaVuSansCondensed.ttf", uni=True)
    except RuntimeError:
        pdf.set_font("Arial","",24)

    if image_path and os.path.exists(image_path):
        original_img = _PILImage.open(image_path)
        iw, ih = original_img.size

        # --- CROP (top half) -------------------------------------------
        # 1) Zapni buď per‑pohádka (např. jen Zlatovláska),
        #    nebo parametricky přes crop_mode="top-half".
        crop_top = (
        crop_mode == "top-half"
        or (crop_mode == "auto" and fairytale_title in {"O Zlatovlásce", "O jednorožci a dráčkovi"})
        )
        if crop_top:
            original_img = original_img.crop((0, 0, iw, ih // 2))
            iw, ih = original_img.size
        # ---------------------------------------------------------------

        # Poloprůhledné pozadí jako dřív
        img_rgba = original_img.convert("RGBA")
        bg = _PILImage.new("RGBA", img_rgba.size, (255, 255, 255, 255))
        img_rgba.putalpha(128)
        final_bg = _PILImage.alpha_composite(bg, img_rgba)

        buf = io.BytesIO()
        final_bg.convert("RGB").save(buf, format="JPEG")
        buf.seek(0)

        # Zvětšení na stránku se zachováním poměru stran
        ar = iw / ih
        if pw / ph > ar:
            bw, bh = pw, pw / ar
        else:
            bh, bw = ph, ph * ar

        # Centrovat; pro top‑half většinou vypadá líp zarovnání k hornímu okraji
        if crop_top:
            x = (pw - bw) / 2
            y = 0  # přiklepnout nahoru
        else:
            x = (pw - bw) / 2
            y = (ph - bh) / 2

        pdf.image(buf, x=x, y=y, w=bw, h=bh)

    # ... (zbytek diplomu beze změny)
    pdf.set_font("DejaVuSans","",36); pdf.set_xy(10,30); pdf.cell(0,10,'Diplom',0,1,'C')
    pdf.set_font("DejaVuSans","",18); pdf.set_xy(10,50)
    pdf.cell(0,10, f'Tento diplom získává za skvělý výkon ve hře Pohádky s {subject_display}', 0, 1, 'C')
    pdf.set_font("DejaVuSans","B",48); pdf.set_xy(10,90); pdf.cell(0,10,username,0,1,'C')
    pdf.set_font("DejaVuSans","",16); pdf.set_xy(10,120)
    pdf.cell(0,10,f'za úspěšné vyřešení {score} úkolů v pohádce "{fairytale_title}"', 0, 1, 'C')
    pdf.set_xy(10,130); pdf.cell(0,10,f'v čase {time_s:.2f} s.', 0, 1, 'C')
    pdf.set_font("DejaVuSans","",12)
    pdf.set_xy(10,160); pdf.cell(0,10,f'Datum a čas: {datetime.datetime.now().strftime("%d.%m.%Y %H:%M")}',0,1,'C')
    pdf.set_xy(10,170); pdf.cell(0,10,f'Úroveň: {level}',0,1,'C')
    pdf.set_xy(10,180); pdf.cell(0,10,f'Téma: {topic_line}',0,1,'C')
    return bytes(pdf.output(dest='S'))

# --- Hlavní obsah ---
if vyber:
    data = fairytales_data[vyber]
    text, moral, img_path_data = data["text"], data["moral"], data["obrazek_path"]
    base, _ = os.path.splitext(img_path_data); image_path=None
    if os.path.exists(os.path.join("obrazky", f"{base}.png")): image_path=os.path.join("obrazky", f"{base}.png")
    elif os.path.exists(os.path.join("obrazky", f"{base}.jpg")): image_path=os.path.join("obrazky", f"{base}.jpg")
    st.session_state.diploma_image_path = image_path

    # reset při změně voleb
    if (st.session_state.last_selected_fairytale != vyber
        or st.session_state.last_selected_class != vyber_tridy
        or st.session_state.last_selected_subject != subject):
        st.session_state.current_task = None
        st.session_state.last_selected_fairytale = vyber
        st.session_state.last_selected_class = vyber_tridy
        st.session_state.last_selected_subject = subject
        st.session_state.feedback_message = ""
        st.session_state.feedback_type = ""
        st.session_state.tasks_solved_for_reveal = 0
        st.session_state.start_time = None
        st.session_state.end_time = None
        st.session_state.final_report = None
        st.session_state.history = []
        st.session_state.game_started = False
        st.session_state.revealed_tiles = [False]*20
        st.session_state.tile_coords = get_tile_coordinates(image_path, 4, 5)
        st.session_state.show_full_fairytale = False
        st.session_state.best_score = 0
        st.session_state.best_time = float('inf')
        st.session_state._cjl_index = 0
        st.session_state._it_index = 0
        st.session_state._it_last_output = ""
        st.session_state._it_last_eval = ""
        st.session_state.current_cjl_task = None
        st.rerun()

    st.title(f"🧙 {vyber}")
    if st.session_state.show_full_fairytale:
        st.markdown(text)
        if st.button("Skrýt celou pohádku"): st.session_state.show_full_fairytale=False; st.rerun()
    else:
        prev = text[:300] + ("…" if len(text)>300 else "")
        st.markdown(prev)
        if st.button("Zobrazit celou pohádku"): st.session_state.show_full_fairytale=True; st.rerun()

    st.divider()
    col_left, col_right = st.columns([1,1])

    with col_left:
        st.markdown("### 📘 Téma")
        db_level = class_to_db_level.get(vyber_tridy, "ZŠ")
        if subject == "MA":
            pozn_list = math_notes_by_level.get(db_level, ["Žádná poznámka."])
        elif subject == "ČJ":
            pozn_list = cjl_notes_by_level.get(db_level, ["Žádná poznámka."])
        else:
            pozn_list = it_notes_by_level.get(db_level, ["Žádná poznámka."])

        if pozn_list:
            with st.expander("📚 Zobrazit"):
                for p in pozn_list:
                    st.markdown(f"- {p}")

        st.subheader("🧩 Úkoly")

        def start_new_game():
            st.session_state.start_time = time.time()
            st.session_state.tasks_solved_for_reveal = 0
            st.session_state.score = 0
            st.session_state.history = []
            st.session_state.feedback_message = ""
            st.session_state.feedback_type = ""
            st.session_state.game_started = True
            st.session_state.revealed_tiles = [False]*20
            st.session_state.tile_coords = get_tile_coordinates(image_path, 4, 5)
            st.session_state.current_task = None
            st.session_state.final_report = None
            st.session_state.achievement_date = None
            st.session_state.end_time = None
            st.session_state._cjl_index = 0
            st.session_state._it_index = 0
            st.session_state._it_last_output = ""
            st.session_state._it_last_eval = ""
            st.session_state.current_cjl_task = None
            st.rerun()

        if not st.session_state.game_started:
            st.info(f"Vyřešte {TASKS_TO_REVEAL} úkolů a odhalte obrázek!")
            if st.button("Začít novou hru", key="start_new_game_initial"):
                start_new_game()
        else:
            if st.session_state.tasks_solved_for_reveal < TASKS_TO_REVEAL:

                # ---------------- MA ----------------
                if subject == "MA":
                    if st.session_state.current_task is None:
                        st.session_state.current_task = generate_math_problem(vyber_tridy)
                    question, correct_answer, problem_type = st.session_state.current_task

                    format_hint = ""
                    if problem_type == "div_remainder":
                        format_hint = "Formát: `podíl zb. zbytek` (např. `5 zb. 2`)."
                    elif problem_type in ["decimal_2dp", "decimal_2dp_number_only", "decimal_or_int"]:
                        format_hint = "Zapiš na 2 desetinná místa. Tečka i čárka jsou povoleny."
                        if problem_type.endswith("number_only"):
                            format_hint += " Zadej čisté číslo (bez jednotky)."
                    elif problem_type == "fraction_reduced":
                        format_hint = "Zlomky zapisuj ve zkráceném tvaru `čitatel/jmenovatel` (např. `3/4`)."
                    elif problem_type == "ratio":
                        format_hint = "Poměr zapisuj jako `a : b` ve zkráceném tvaru."
                    elif problem_type == "quadratic_one_of_two":
                        format_hint = "Stačí zadat jednu z hodnot, které rovnici vyhovují."

                    with st.container():
                        c1,c2 = st.columns([4,1])
                        with c1:
                            st.markdown(f"##### ✏️ {question}")
                            if format_hint: st.caption("💡 " + format_hint)
                        with c2:
                            st.markdown(f"🏅 **Skóre:** {st.session_state.tasks_solved_for_reveal}/{TASKS_TO_REVEAL}")

                        with st.form("math_form", clear_on_submit=True):
                            a1,a2 = st.columns([3,1])
                            with a1:
                                ans = st.text_input("Tvoje odpověď:", key="math_answer_input", label_visibility="collapsed", placeholder="Sem napiš svou odpověď…")
                            with a2:
                                ok = st.form_submit_button("Odeslat")

                    if st.session_state.feedback_message:
                        (st.success if st.session_state.feedback_type=="success" else st.error)(st.session_state.feedback_message)

                    if 'ok' in locals() and ok:
                        is_correct = False
                        user_disp = ans
                        corr_disp = correct_answer if not isinstance(correct_answer, tuple) else " nebo ".join(correct_answer)
                        try:
                            if problem_type == "int":
                                val = int(ans.replace(" ", ""))
                                is_correct = (str(val) == str(correct_answer))
                            elif problem_type == "div_remainder":
                                uq, ur = parse_div_remainder(ans)
                                cq, cr = parse_div_remainder(correct_answer)
                                is_correct = (uq == cq and ur == cr)
                            elif problem_type in ["decimal_2dp","decimal_2dp_number_only","decimal_or_int"]:
                                u = normalize_decimal(ans); c = float(str(correct_answer).replace(",", "."))
                                is_correct = approx_equal(u, c, 1e-2)
                            elif problem_type == "fraction_reduced":
                                is_correct = fraction_equal_reduced(ans, correct_answer)
                            elif problem_type == "ratio":
                                ua, ub = parse_ratio(ans); ca, cb = parse_ratio(correct_answer)
                                is_correct = (ua == ca and ub == cb)
                            elif problem_type == "quadratic_one_of_two":
                                try:
                                    v = int(float(ans.replace(",", ".").strip()))
                                    is_correct = (str(v) in set(correct_answer))
                                except:
                                    is_correct = (ans.strip() in set(correct_answer))
                            else:
                                try:
                                    u = normalize_decimal(ans); c = normalize_decimal(str(correct_answer))
                                    is_correct = approx_equal(u, c, 1e-2)
                                except:
                                    is_correct = (str(ans).strip() == str(correct_answer).strip())
                        except Exception:
                            is_correct = False

                        if is_correct:
                            st.session_state.feedback_message = "Správně! 🎉"; st.session_state.feedback_type="success"
                            st.session_state.tasks_solved_for_reveal += 1
                            st.session_state.history.append((question, user_disp, corr_disp, "✅ správně"))
                            unrevealed = [i for i,r in enumerate(st.session_state.revealed_tiles) if not r]
                            if unrevealed: st.session_state.revealed_tiles[random.choice(unrevealed)] = True
                        else:
                            st.session_state.feedback_message = f"Nesprávně. ❌ Správná odpověď: {corr_disp}"; st.session_state.feedback_type="error"
                            st.session_state.history.append((question, user_disp, corr_disp, "❌ špatně"))

                        st.session_state.current_task = None
                        st.rerun()

                # ---------------- ČJ ----------------
                elif subject == "ČJ":
                    level_tasks = cjl_tasks_by_level.get(vyber_tridy, {}).get("rounds", [])
                    flat = [t for rnd in level_tasks for t in rnd]

                    if not flat:
                        st.warning("Pro tuto třídu zatím nejsou ČJ úlohy.")
                    else:
                        # Udrž náhodnou otázku do odeslání
                        if st.session_state.current_cjl_task is None:
                            st.session_state.current_cjl_task = random.choice(flat)
                        task = st.session_state.current_cjl_task

                        with st.form("cjl_form", clear_on_submit=False):
                            c1, c2 = st.columns([4,1])
                            with c1:
                                st.markdown(f"##### ✏️ {task['text']}")
                            with c2:
                                st.markdown(f"🏅 **Skóre:** {st.session_state.tasks_solved_for_reveal}/{TASKS_TO_REVEAL}")

                            choice = st.radio(
                                "Vyber odpověď:",
                                options=["a","b","c"],
                                index=None,
                                format_func=lambda x: task["options"][ord(x)-97],
                                key=f"cjl_choice_{hash(task['text']) % (10**8)}"
                            )
                            ok_cjl = st.form_submit_button("Odeslat")

                        # ENTER -> klikne na tlačítko "Odeslat"
                        st.markdown("""
                        <script>
                        (function(){
                          const root = window.parent.document;
                          function findSubmit(){
                            const btns = Array.from(root.querySelectorAll('button'));
                            return btns.find(b => b.innerText.trim() === 'Odeslat');
                          }
                          function handler(e){
                            if (e.key === 'Enter') {
                              const btn = findSubmit();
                              if (btn) btn.click();
                            }
                          }
                          root.addEventListener('keydown', handler);
                        })();
                        </script>
                        """, unsafe_allow_html=True)

                        if st.session_state.feedback_message:
                            (st.success if st.session_state.feedback_type=="success" else st.error)(st.session_state.feedback_message)

                        if ok_cjl:
                            if choice is None:
                                st.warning("Než odešleš, nejdřív prosím vyber jednu z možností.")
                            else:
                                corr = task["correct_option"]
                                if choice == corr:
                                    st.session_state.feedback_message = "Správně! 🎉"
                                    st.session_state.feedback_type = "success"
                                    st.session_state.tasks_solved_for_reveal += 1
                                    st.session_state.history.append(
                                        (task["text"],
                                         f"({choice}) {task['options'][ord(choice)-97]}",
                                         f"({corr}) {task['options'][ord(corr)-97]}",
                                         "✅ správně")
                                    )
                                    unrevealed = [i for i,r in enumerate(st.session_state.revealed_tiles) if not r]
                                    if unrevealed:
                                        st.session_state.revealed_tiles[random.choice(unrevealed)] = True
                                else:
                                    st.session_state.feedback_message = f"Nesprávně. ❌ Správná odpověď byla: ({corr}) {task['options'][ord(corr)-97]}"
                                    st.session_state.feedback_type = "error"
                                    st.session_state.history.append(
                                        (task["text"],
                                         f"({choice}) {task['options'][ord(choice)-97]}",
                                         f"({corr}) {task['options'][ord(corr)-97]}",
                                         "❌ špatně")
                                    )

                                # vyber novou náhodnou otázku příště
                                st.session_state.current_cjl_task = None
                                st.rerun()

                # ---------------- IT ----------------
                else:
                    tasks = it_tasks_by_level.get(vyber_tridy, [])
                    if not tasks:
                        st.warning("Pro tuto třídu zatím nejsou IT úlohy.")
                    else:
                        idx = st.session_state._it_index % len(tasks)
                        task = tasks[idx]
                        st.markdown(f"##### 💻 {task['prompt']}")

                        code_key = f"it_code_{idx}"
                        code = st.text_area(
                            "Tvůj Python kód:",
                            value=st.session_state.get(code_key, task.get("starter","")),
                            height=160,
                            key=code_key,
                            placeholder="Sem napiš svůj kód…"
                        )

                        # Řádek 1: Spustit kód + okno s výstupem
                        c_run_out = st.columns([1,3])
                        run = c_run_out[0].button("Spustit kód")
                        if run:
                            ok_run, out = run_user_code_capture_stdout(code)
                            st.session_state._it_last_output = out if ok_run else out
                        with c_run_out[1]:
                            st.caption("Výstup programu:")
                            st.code(st.session_state._it_last_output or "(žádný výstup)")

                        # Řádek 2: Vyhodnotit + hodnocení
                        c_eval = st.columns([1,3])
                        eval_btn = c_eval[0].button("Vyhodnotit")
                        if eval_btn:
                            ok_run, out = run_user_code_capture_stdout(code)
                            st.session_state._it_last_output = out if ok_run else out
                            expected = task["expected_stdout"].strip()
                            if not ok_run:
                                st.session_state._it_last_eval = f"Chyba běhu: {out}"
                                st.session_state.feedback_message = out
                                st.session_state.feedback_type = "error"
                                st.session_state.history.append((task["prompt"], out, expected, "❌ chyba běhu"))
                            else:
                                if out.strip() == expected:
                                    st.session_state._it_last_eval = "Správně! 🎉"
                                    st.session_state.feedback_message = "Správně! 🎉"
                                    st.session_state.feedback_type = "success"
                                    st.session_state.tasks_solved_for_reveal += 1
                                    st.session_state.history.append((task["prompt"], out, expected, "✅ správně"))
                                    st.session_state._it_index += 1
                                    unrevealed = [i for i,r in enumerate(st.session_state.revealed_tiles) if not r]
                                    if unrevealed: st.session_state.revealed_tiles[random.choice(unrevealed)] = True
                                else:
                                    st.session_state._it_last_eval = f"Nesprávně. Očekáváno: `{expected}`; tvůj výstup: `{out}`"
                                    st.session_state.feedback_message = f"Nesprávně. ❌ Očekáváno: `{expected}`; tvůj výstup: `{out}`"
                                    st.session_state.feedback_type = "error"
                                    st.session_state.history.append((task["prompt"], out, expected, "❌ špatně"))
                            st.rerun()

                        with c_eval[1]:
                            st.caption("Hodnocení:")
                            if st.session_state._it_last_eval:
                                if "Správně" in st.session_state._it_last_eval:
                                    st.success(st.session_state._it_last_eval)
                                elif "Chyba" in st.session_state._it_last_eval:
                                    st.error(st.session_state._it_last_eval)
                                else:
                                    st.error(st.session_state._it_last_eval)
                            else:
                                st.info("Zatím nevyhodnoceno.")

                        st.markdown(f"🏅 **Skóre:** {st.session_state.tasks_solved_for_reveal}/{TASKS_TO_REVEAL}")

            else:
                st.snow()
                if st.session_state.end_time is None:
                    st.session_state.end_time = time.time()
                    st.session_state.achievement_date = datetime.datetime.now()
                    total = st.session_state.end_time - st.session_state.start_time
                    correct = sum(1 for *_ , status in st.session_state.history if status=="✅ správně")
                    incorrect = len(st.session_state.history) - correct
                    is_best=False
                    if correct > st.session_state.best_score: st.session_state.best_score=correct; is_best=True
                    if total < st.session_state.best_time: st.session_state.best_time=total; is_best=True
                    report = f"#### ✨ Skvěle!\n- Správně: **{correct}**\n- Nesprávně: **{incorrect}**\n- Čas (20 úkolů): **{total:.2f}** s\n"
                    if is_best: report += "\n**🏆 Nový osobní rekord!**"
                    st.session_state.final_report = report
                    st.session_state.score = st.session_state.tasks_solved_for_reveal
                st.success("Vyřešil/a jsi všech 20 úkolů!")

        # Historie (všechny předměty)
        if st.checkbox("📜 Zobrazit historii odpovědí", key="show_history"):
            st.markdown("---"); st.subheader("Historie řešení")
            if not st.session_state.history:
                st.info("Zatím žádné odpovědi.")
            else:
                for i, item in enumerate(reversed(st.session_state.history), 1):
                    q, a_user, a_correct, status = item
                    st.markdown(f"{i}. **{q}** → tvoje: `{a_user}` | správně: `{a_correct}` — {status}")

        if st.session_state.final_report:
            st.subheader("🏆 Výsledková listina")
            st.info(st.session_state.final_report)
            st.subheader("📜 Vytvořit diplom")
            st.markdown(f"Nejlepší výsledek v „{vyber}“ ({vyber_tridy}): **{st.session_state.best_score}** úkolů v **{st.session_state.best_time:.2f} s**.")
            diploma_name = st.text_input("Jméno na diplom:", value="")

            if diploma_name and st.session_state.best_score>0 and st.session_state.achievement_date:
                if subject=="MA":
                    subject_display = "Matematikou"
                    notes = math_notes_by_level.get(db_level, ["Téma není k dispozici."])
                elif subject=="ČJ":
                    subject_display = "Češtinou"
                    notes = cjl_notes_by_level.get(db_level, ["Téma není k dispozici."])
                else:
                    subject_display = "Informatikou (Python)"
                    notes = it_notes_by_level.get(db_level, ["Téma není k dispozici."])
                topic_line = notes[0] if notes else "Téma není k dispozici."

                pdf = generate_diploma_pdf(
                    username=diploma_name,
                    score=st.session_state.best_score,
                    time_s=st.session_state.best_time,
                    fairytale_title=vyber,
                    achievement_date=st.session_state.achievement_date,
                    level=vyber_tridy,
                    subject_display=subject_display,
                    topic_line=topic_line,
                    image_path=st.session_state.diploma_image_path
                )
                if pdf:
                    st.download_button("Stáhnout diplom PDF", data=pdf, file_name=f"diplom_{diploma_name}.pdf", mime="application/pdf")

        if st.session_state.game_started and st.session_state.tasks_solved_for_reveal>=TASKS_TO_REVEAL:
            if st.button("Začít novou hru", key="restart_game_final"):
                st.session_state.game_started=False
                st.rerun()

    with col_right:
        st.subheader("🖼️ Obrázek")
        image_path = st.session_state.diploma_image_path
        if image_path and os.path.exists(image_path):
            if st.session_state.tasks_solved_for_reveal>=TASKS_TO_REVEAL:
                st.image(image_path, use_container_width=True, caption=f"Gratuluji, obrázek je kompletní! ({st.session_state.tasks_solved_for_reveal}/{TASKS_TO_REVEAL})")
            else:
                img = _PILImage.open(image_path); draw = ImageDraw.Draw(img)
                if not st.session_state.game_started:
                    tiles = range(TASKS_TO_REVEAL); caption="Začněte novou hru a odhalte obrázek!"
                else:
                    tiles = [i for i,r in enumerate(st.session_state.revealed_tiles) if not r]
                    caption=f"Odhalených {st.session_state.tasks_solved_for_reveal}/{TASKS_TO_REVEAL} políček"
                if st.session_state.tile_coords:
                    for i in tiles:
                        if i < len(st.session_state.tile_coords):
                            coords = st.session_state.tile_coords[i]
                            draw.rectangle(coords, fill="black")
                buf = io.BytesIO(); img.save(buf, format="PNG")
                st.image(buf, use_container_width=True, caption=caption)
        else:
            st.warning("Obrázek k zobrazení nebyl nalezen.")

    st.divider()
    st.subheader("⭐ Mravní ponaučení")
    if moral: st.info(moral)
    else: st.warning("Ponaučení není zadáno.")
else:
    st.warning("Nebyla vybrána žádná pohádka.")


