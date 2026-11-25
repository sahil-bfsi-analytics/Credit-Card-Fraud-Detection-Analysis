"""
Synthetic Credit Card Fraud Detection dataset generator (Indian banking style).
100% synthetic. No real customers, cards, banks or credentials.
Outputs are written to ./output/
"""
import os
import math
from collections import namedtuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

SEED = 20260511
rng = np.random.default_rng(SEED)

START = datetime(2026, 5, 1, 0, 0, 0)
END = datetime(2026, 10, 31, 23, 59, 59)
SNAPSHOT = datetime(2026, 11, 10)          # date used to age chargebacks / open investigations
TOTAL_ROWS, N_DUP, N_FRAUD, N_CUST = 10000, 30, 150, 650
N_UNIQUE = TOTAL_ROWS - N_DUP              # 9,970 unique clean transactions
N_LEGIT = N_UNIQUE - N_FRAUD               # 9,820
BASE_LOGIT = float(os.environ.get("BASE_LOGIT", "-4.1"))

OUT = "output"
os.makedirs(OUT, exist_ok=True)


# ----------------------------------------------------------------- helpers
def wchoice(items, weights):
    w = np.array(weights, dtype=float)
    w = w / w.sum()
    return items[int(rng.choice(len(items), p=w))]


def wc(d):
    return wchoice(list(d.keys()), list(d.values()))


def rint(a, b):
    return int(rng.integers(a, b + 1))


def rch(lst):
    return lst[int(rng.integers(0, len(lst)))]


def unif(a, b):
    return float(rng.uniform(a, b))


HEX = "0123456789ABCDEF"
USED = {k: set() for k in ["mer", "trm", "dev", "tkn", "acc"]}


def uid(kind, prefix, n, hexa=False):
    while True:
        if hexa:
            s = prefix + "".join(HEX[i] for i in rng.integers(0, 16, n))
        else:
            s = prefix + "".join(str(i) for i in rng.integers(0, 10, n))
        if s not in USED[kind]:
            USED[kind].add(s)
            return s


def haversine(a, b):
    la1, lo1, la2, lo2 = map(math.radians, [a[0], a[1], b[0], b[1]])
    d = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371.0 * 2 * math.asin(math.sqrt(d))


# ----------------------------------------------------------------- geography
IN_CITIES = {
    'Mumbai': (19.0760, 72.8777, 14), 'Delhi': (28.6139, 77.2090, 13), 'Bengaluru': (12.9716, 77.5946, 11),
    'Hyderabad': (17.3850, 78.4867, 8), 'Chennai': (13.0827, 80.2707, 7), 'Kolkata': (22.5726, 88.3639, 6),
    'Pune': (18.5204, 73.8567, 6), 'Ahmedabad': (23.0225, 72.5714, 5), 'Jaipur': (26.9124, 75.7873, 3),
    'Surat': (21.1702, 72.8311, 3), 'Lucknow': (26.8467, 80.9462, 2.5), 'Nagpur': (21.1458, 79.0882, 2),
    'Indore': (22.7196, 75.8577, 2.5), 'Bhopal': (23.2599, 77.4126, 2), 'Patna': (25.5941, 85.1376, 2),
    'Vadodara': (22.3072, 73.1812, 2), 'Rajkot': (22.3039, 70.8022, 1.5), 'Chandigarh': (30.7333, 76.7794, 2),
    'Kochi': (9.9312, 76.2673, 2.5), 'Coimbatore': (11.0168, 76.9558, 2), 'Guwahati': (26.1445, 91.7362, 1.5),
    'Nashik': (19.9975, 73.7898, 1.5), 'Gurugram': (28.4595, 77.0266, 3), 'Noida': (28.5355, 77.3910, 3),
    'Thiruvananthapuram': (8.5241, 76.9366, 1.5), 'Visakhapatnam': (17.6868, 83.2185, 2),
    'Mysuru': (12.2958, 76.6394, 1), 'Panaji': (15.4909, 73.8278, 1.5), 'Udaipur': (24.5854, 73.7125, 1),
}
INTL = {
    'United Arab Emirates': [('Dubai', 25.2048, 55.2708), ('Abu Dhabi', 24.4539, 54.3773)],
    'Singapore': [('Singapore', 1.3521, 103.8198)],
    'United Kingdom': [('London', 51.5074, -0.1278), ('Manchester', 53.4808, -2.2426)],
    'United States': [('New York', 40.7128, -74.0060), ('San Francisco', 37.7749, -122.4194),
                      ('Los Angeles', 34.0522, -118.2437), ('Chicago', 41.8781, -87.6298)],
    'Thailand': [('Bangkok', 13.7563, 100.5018), ('Phuket', 7.8804, 98.3923)],
    'France': [('Paris', 48.8566, 2.3522)],
    'Germany': [('Frankfurt', 50.1109, 8.6821), ('Berlin', 52.5200, 13.4050)],
    'Hong Kong': [('Hong Kong', 22.3193, 114.1694)],
    'Malaysia': [('Kuala Lumpur', 3.1390, 101.6869)],
    'Australia': [('Sydney', -33.8688, 151.2093)],
    'Canada': [('Toronto', 43.6532, -79.3832)],
    'Ireland': [('Dublin', 53.3498, -6.2603)],
    'Netherlands': [('Amsterdam', 52.3676, 4.9041)],
    'Nigeria': [('Lagos', 6.5244, 3.3792)],
    'Vietnam': [('Ho Chi Minh City', 10.8231, 106.6297)],
    'Romania': [('Bucharest', 44.4268, 26.1025)],
    'Turkey': [('Istanbul', 41.0082, 28.9784)],
    'Indonesia': [('Jakarta', -6.2088, 106.8456)],
}
CITY = {('India', k): (v[0], v[1]) for k, v in IN_CITIES.items()}
for _c, _l in INTL.items():
    for _city, _la, _lo in _l:
        CITY[(_c, _city)] = (_la, _lo)

Loc = namedtuple('Loc', 'country city lat lon')
IN_NAMES = list(IN_CITIES)
IN_W = [IN_CITIES[k][2] for k in IN_NAMES]
ONL_CITY_N = ['Bengaluru', 'Mumbai', 'Delhi', 'Gurugram', 'Hyderabad', 'Pune', 'Chennai', 'Noida']
ONL_CITY_W = [25, 25, 12, 12, 8, 8, 5, 5]


def india_loc(name):
    la, lo, _ = IN_CITIES[name]
    return Loc('India', name, la, lo)


def intl_loc(country):
    city, la, lo = rch(INTL[country])
    return Loc(country, city, la, lo)


TRIP_C = {'United Arab Emirates': 25, 'Singapore': 12, 'United Kingdom': 12, 'United States': 14, 'Thailand': 10,
          'France': 4, 'Germany': 3, 'Hong Kong': 4, 'Malaysia': 5, 'Australia': 3, 'Canada': 2,
          'Indonesia': 3, 'Turkey': 1, 'Netherlands': 2}
ONL_FC = {'United States': 40, 'United Kingdom': 10, 'Singapore': 12, 'Ireland': 12, 'Netherlands': 6,
          'United Arab Emirates': 6, 'Germany': 4, 'Canada': 4, 'Australia': 3, 'Hong Kong': 3}
VPN_C = {'United States': 40, 'United Kingdom': 15, 'Singapore': 15, 'Netherlands': 10, 'Germany': 10,
         'United Arab Emirates': 10}
FR_MERCH = {'United States': 25, 'United Kingdom': 10, 'Singapore': 10, 'Hong Kong': 8, 'Nigeria': 8,
            'Vietnam': 6, 'Romania': 6, 'United Arab Emirates': 10, 'Turkey': 6, 'Indonesia': 5, 'Thailand': 6}
FR_IP = {'Nigeria': 14, 'Romania': 10, 'Vietnam': 10, 'United States': 18, 'Turkey': 8, 'Indonesia': 8,
         'United Kingdom': 6, 'Hong Kong': 6, 'Singapore': 6, 'United Arab Emirates': 8, 'Thailand': 6}

# ----------------------------------------------------------------- categories
POS_CATS = {'Grocery': 24, 'Fuel': 14, 'Restaurants': 18, 'Healthcare': 7, 'Electronics': 7, 'Jewellery': 3,
            'Fashion': 11, 'Travel': 3, 'Entertainment': 4, 'Education': 1}
INTL_POS = {'Restaurants': 25, 'Fashion': 18, 'Travel': 16, 'Grocery': 8, 'Entertainment': 10, 'Jewellery': 5,
            'Electronics': 8, 'Healthcare': 2, 'Fuel': 4}
ONL_CATS = {'E-commerce': 32, 'Travel': 14, 'Entertainment': 10, 'Utilities': 10, 'Electronics': 8, 'Fashion': 8,
            'Grocery': 6, 'Restaurants': 5, 'Education': 3, 'Healthcare': 2, 'Gaming': 3, 'Gift Cards': 2,
            'Money Transfer': 1.5, 'Jewellery': 1}
ONL_FOREIGN = {'E-commerce': 30, 'Entertainment': 25, 'Travel': 20, 'Electronics': 8, 'Education': 7, 'Fashion': 10}
BASE_AMT = {'Grocery': 900, 'Fuel': 2200, 'Electronics': 15000, 'Restaurants': 1100, 'Travel': 9000,
            'E-commerce': 1800, 'Healthcare': 2200, 'Entertainment': 600, 'Jewellery': 30000, 'ATM': 5000,
            'Fashion': 2500, 'Utilities': 1600, 'Education': 8000, 'Gaming': 700, 'Gift Cards': 1500,
            'Money Transfer': 6000}
HR_P = {'Gaming': 0.7, 'Gift Cards': 0.6, 'Money Transfer': 0.7, 'Jewellery': 0.12, 'Electronics': 0.08,
        'E-commerce': 0.07, 'Travel': 0.06, 'Entertainment': 0.05, 'Fashion': 0.03, 'ATM': 0.0}

DAY_HW = [1, .5, .3, .3, .4, .8, 2, 4, 5, 6, 6, 6, 6, 6, 5.5, 5, 5, 5.5, 6, 6, 5, 3, 2, 1.5]
FR_NIGHT_HW = [4, 4, 4, 3.5, 3, 2, 1, 1, 1.5, 2, 2, 2, 2, 2, 2, 2, 2, 2.5, 3, 3, 3.5, 4, 4, 4.5]


def rand_time(hw):
    day = rint(0, (END.date() - START.date()).days)
    hour = wchoice(list(range(24)), hw)
    return START + timedelta(days=day, hours=hour, minutes=rint(0, 59), seconds=rint(0, 59))


# ----------------------------------------------------------------- merchants
class Merch:
    pass


M_BY_KEY = {}


def new_merchant(country, city, cat, hr=None):
    m = Merch()
    m.id = uid('mer', 'MER', 6)
    m.cat, m.country, m.city = cat, country, city
    m.lat, m.lon = CITY[(country, city)]
    m.hr = bool(rng.random() < HR_P.get(cat, 0.02)) if hr is None else hr
    m.terms = [uid('trm', 'TRM', 6) for _ in range(rint(2, 5) if cat == 'ATM' else rint(1, 3))]
    M_BY_KEY.setdefault((country, city, cat), []).append(m)
    return m


def get_merchant(country, city, cat, want_hr=False, new_p=0.15):
    lst = M_BY_KEY.get((country, city, cat), [])
    if want_hr:
        hrl = [m for m in lst if m.hr]
        if hrl and rng.random() > 0.2:
            return rch(hrl)
        return new_merchant(country, city, cat, hr=True)
    if lst and rng.random() > new_p:
        return rch(lst)
    return new_merchant(country, city, cat)


# ----------------------------------------------------------------- customers
class Cust:
    pass


def make_trip(c, intl):
    length = rint(4, 12) if intl else rint(2, 6)
    s = START + timedelta(days=rint(0, 183 - length), hours=rint(0, 23))
    e = s + timedelta(days=length)
    loc = intl_loc(wc(TRIP_C)) if intl else india_loc(wchoice(IN_NAMES, IN_W))
    c.trips.append((s, e, loc))


custs = []
for i in range(N_CUST):
    c = Cust()
    c.id = f"CUST{10001 + i}"
    c.home = india_loc(wchoice(IN_NAMES, IN_W))
    c.tier = wchoice([0.55, 1.0, 2.4], [35, 45, 20])
    c.avg_base = c.tier * 2200 * float(rng.lognormal(0, 0.25))
    n_acc = 1 if rng.random() < 0.88 else 2
    c.accts = [uid('acc', 'ACC', 10) for _ in range(n_acc)]
    c.cards = [(uid('tkn', 'TKN', 12, True), c.accts[rint(0, n_acc - 1)]) for _ in range(wchoice([1, 2, 3], [60, 30, 10]))]
    c.devices = [uid('dev', 'DEV', 8, True) for _ in range(wchoice([1, 2], [60, 40]))]
    c.base_devices = set(c.devices)
    c.online_pref = float(np.clip(rng.normal(1, 0.35), 0.4, 1.8))
    c.weight = float(rng.lognormal(0, 1.0))
    c.trips = []
    c.legit_ts = []
    if rng.random() < 0.22:
        for _ in range(wchoice([1, 2], [75, 25])):
            make_trip(c, False)
    if rng.random() < 0.09:
        make_trip(c, True)
        if rng.random() < 0.2:
            make_trip(c, True)
    custs.append(c)


def location_at(c, t):
    for s, e, loc in c.trips:
        if s <= t <= e:
            return loc
    if rng.random() < 0.94:
        return c.home
    return india_loc(wchoice(IN_NAMES, IN_W))


def ipgeo(country, home):
    if country == home.country:
        return (home.lat, home.lon)
    city = INTL[country][0]
    return (city[1], city[2])


# ----------------------------------------------------------------- legit transactions
def make_legit(c, t, loc):
    abroad = loc.country != 'India'
    w = [60, 30, 10] if abroad else [52, 40 * c.online_pref, 8]
    ch = wchoice(['POS', 'Online', 'ATM'], w)
    device = ip = term = None
    if ch == 'ATM':
        cat = 'ATM'
        m = get_merchant(loc.country, loc.city, cat, new_p=0.05)
    elif ch == 'POS':
        cat = wc(INTL_POS if abroad else POS_CATS)
        m = get_merchant(loc.country, loc.city, cat)
    else:
        u = rng.random()
        if abroad:
            mc = 'India' if u < 0.5 else (loc.country if u < 0.8 else wc(ONL_FC))
        else:
            mc = 'India' if u < 0.93 else wc(ONL_FC)
        if mc == 'India':
            cat = wc(ONL_CATS)
            city = wchoice(ONL_CITY_N, ONL_CITY_W)
        else:
            cat = wc(ONL_FOREIGN)
            city = rch(INTL[mc])[0]
        m = get_merchant(mc, city, cat)
    base = BASE_AMT[cat] * c.tier * float(rng.lognormal(0, 0.65)) * (1.4 if abroad else 1.0)
    if cat == 'ATM':
        amt = float(min(40000, max(500, round(base / 500) * 500)))
    else:
        amt = round(float(np.clip(base, 100, 200000)), 2)
    card = wchoice(c.cards, [60, 30, 10][:len(c.cards)])
    if ch == 'Online':
        if rng.random() < 0.03:
            device = uid('dev', 'DEV', 8, True)
            c.devices.append(device)
        else:
            device = rch(c.devices)
        ip = loc.country
        if rng.random() < 0.015:
            ip = wc(VPN_C)
        geo = ipgeo(ip, loc)
        foreign_m = m.country != 'India'
        entry = 'Manual Entry' if rng.random() < (0.35 if foreign_m else 0.08) else 'Online Authentication'
    else:
        geo = (m.lat, m.lon)
        term = rch(m.terms)
        if ch == 'ATM':
            entry = 'ATM PIN'
        elif amt < 5000 and rng.random() < 0.5:
            entry = 'Contactless'
        else:
            entry = wchoice(['Chip', 'Swipe', 'Manual Entry'], [90, 8, 2])
    return dict(c=c, t=t, ch=ch, cat=cat, m=m, amt=amt, card=card, device=device, ip=ip, geo=geo,
                entry=entry, term=term, label=0, scen='Legitimate')


all_tx = []
wts = np.array([c.weight for c in custs])
counts = 3 + rng.multinomial(N_LEGIT - 3 * N_CUST, wts / wts.sum())
for c, n in zip(custs, counts):
    times, locs = [], []
    for k in range(int(n)):
        if k > 0 and rng.random() < 0.17:          # short follow-up purchase sessions
            j = rint(0, k - 1)
            t = times[j] + timedelta(minutes=min(float(rng.exponential(35)) + 1, 240))
            if t > END:
                t = times[j] - timedelta(minutes=rint(1, 120))
            if t < START:
                t = times[j]
            loc = locs[j]
        else:
            t = rand_time(DAY_HW)
            loc = location_at(c, t)
        t = t.replace(microsecond=0)
        times.append(t)
        locs.append(loc)
        all_tx.append(make_legit(c, t, loc))
        c.legit_ts.append(t)

# ----------------------------------------------------------------- fraud scenarios
FR_DEVS = [uid('dev', 'DEV', 8, True) for _ in range(14)]
fw = np.array([c.weight ** 0.4 for c in custs])
fw = fw / fw.sum()


def fcust():
    return custs[int(rng.choice(len(custs), p=fw))]


def fraud_device():
    return rch(FR_DEVS) if rng.random() < 0.55 else uid('dev', 'DEV', 8, True)


def fraud_ip(mcountry=None):
    u = rng.random()
    if u < 0.15:
        return 'India'
    if mcountry and u < 0.5:
        return mcountry
    return wc(FR_IP)


def anchored_time(c, lo, hi, p, hw):
    if c.legit_ts and rng.random() < p:
        t = rch(c.legit_ts) + timedelta(minutes=rint(lo, hi), seconds=rint(0, 59))
        if START <= t <= END:
            return t
    return rand_time(hw)


def far_india_loc(home):
    for _ in range(50):
        l = india_loc(wchoice(IN_NAMES, IN_W))
        if haversine((home.lat, home.lon), (l.lat, l.lon)) > 300:
            return l
    return india_loc('Delhi' if home.city != 'Delhi' else 'Mumbai')


def ftx(c, t, ch, cat, m, amt, device, ip, entry, term, card):
    t = min(t, END).replace(microsecond=0)
    if ch == 'Online':
        geo = ipgeo(ip, c.home)
    else:
        geo = (m.lat, m.lon)
    return dict(c=c, t=t, ch=ch, cat=cat, m=m, amt=float(amt), card=card, device=device, ip=ip, geo=geo,
                entry=entry, term=term, label=1, scen='')


def fraud_online_merchant(cats, foreign_p, hr_p):
    cat = wc(cats)
    if rng.random() < foreign_p:
        country = wc(FR_MERCH)
        city = rch(INTL[country])[0]
    else:
        country, city = 'India', wchoice(ONL_CITY_N, ONL_CITY_W)
    return get_merchant(country, city, cat, want_hr=bool(rng.random() < hr_p), new_p=0.3)


def scen_A():   # card testing burst
    c = fcust()
    card = rch(c.cards)
    t = anchored_time(c, 60, 600, 0.35, FR_NIGHT_HW)
    dev, ip = fraud_device(), fraud_ip()
    nb = rint(3, 5)
    cats = {'Gaming': 25, 'Gift Cards': 20, 'E-commerce': 25, 'Entertainment': 20, 'Money Transfer': 10}
    m = fraud_online_merchant(cats, 0.55, 0.6)
    out = []
    for i in range(nb):
        if i > 0:
            t = t + timedelta(minutes=rint(1, 6), seconds=rint(0, 59))
            if rng.random() < 0.4:
                m = fraud_online_merchant(cats, 0.55, 0.6)
        amt = unif(3000, 15000) if (i == nb - 1 and rng.random() < 0.2) else unif(100, 1500)
        entry = 'Manual Entry' if rng.random() < 0.55 else 'Online Authentication'
        out.append(ftx(c, t, 'Online', m.cat, m, round(amt, 2), dev, ip, entry, None, card))
    return out


def scen_B():   # international card-not-present
    c = fcust()
    card = rch(c.cards)
    t = anchored_time(c, 30, 600, 0.5, FR_NIGHT_HW)
    cats = {'E-commerce': 30, 'Electronics': 25, 'Travel': 20, 'Gift Cards': 10, 'Jewellery': 10, 'Fashion': 5}
    dev = fraud_device()
    out = []
    for i in range(rint(1, 2)):
        m = fraud_online_merchant(cats, 1.0, 0.45)
        amt = float(np.clip(c.avg_base * unif(2.5, 10), 3000, 200000))
        ip = fraud_ip(m.country)
        entry = 'Manual Entry' if rng.random() < 0.5 else 'Online Authentication'
        out.append(ftx(c, t, 'Online', m.cat, m, round(amt, 2), dev, ip, entry, None, card))
        t = t + timedelta(minutes=rint(5, 60))
    return out


def scen_C():   # account takeover, domestic online
    c = fcust()
    card = rch(c.cards)
    t = anchored_time(c, 30, 900, 0.5, FR_NIGHT_HW)
    cats = {'Electronics': 25, 'Gift Cards': 20, 'E-commerce': 25, 'Money Transfer': 10, 'Gaming': 10,
            'Jewellery': 5, 'Travel': 5}
    dev = fraud_device()
    ip = 'India' if rng.random() < 0.7 else wc(FR_IP)
    out = []
    for i in range(rint(1, 3)):
        m = fraud_online_merchant(cats, 0.0, 0.5)
        mult = unif(0.6, 1.5) if rng.random() < 0.35 else unif(1.5, 8)
        amt = float(np.clip(c.avg_base * mult, 300, 200000))
        entry = 'Online Authentication' if rng.random() < 0.7 else 'Manual Entry'
        out.append(ftx(c, t, 'Online', m.cat, m, round(amt, 2), dev, ip, entry, None, card))
        t = t + timedelta(minutes=rint(2, 40))
    return out


def scen_D():   # lost / stolen card POS spree
    c = fcust()
    card = rch(c.cards)
    loc = far_india_loc(c.home) if rng.random() < 0.6 else c.home
    t = anchored_time(c, 45, 420, 0.7, DAY_HW)
    cats = {'Electronics': 25, 'Jewellery': 15, 'Fuel': 15, 'Fashion': 15, 'Restaurants': 10, 'Grocery': 10,
            'Travel': 10}
    out = []
    for i in range(rint(2, 4)):
        cat = wc(cats)
        m = get_merchant(loc.country, loc.city, cat, new_p=0.4)
        amt = float(np.clip(c.avg_base * unif(1, 6) * (2 if cat == 'Jewellery' else 1), 300, 150000))
        if amt < 5000 and rng.random() < 0.5:
            entry = 'Contactless'
        else:
            entry = wchoice(['Swipe', 'Chip', 'Manual Entry'], [55, 40, 5])
        out.append(ftx(c, t, 'POS', cat, m, round(amt, 2), None, None, entry, rch(m.terms), card))
        t = t + timedelta(minutes=rint(8, 90))
    return out


def scen_E():   # ATM cash-out (skimmed card), usually distant / foreign
    c = fcust()
    card = rch(c.cards)
    if rng.random() < 0.45:
        loc = intl_loc(wc(FR_MERCH))
    else:
        loc = far_india_loc(c.home)
    t = anchored_time(c, 60, 600, 0.6, FR_NIGHT_HW)
    out = []
    for i in range(rint(1, 3)):
        m = get_merchant(loc.country, loc.city, 'ATM', new_p=0.3)
        out.append(ftx(c, t, 'ATM', 'ATM', m, float(rint(10, 80) * 500), None, None, 'ATM PIN', rch(m.terms), card))
        t = t + timedelta(minutes=rint(3, 15))
    return out


def scen_F():   # low-value subscription / small online fraud
    c = fcust()
    card = rch(c.cards)
    t = rand_time(DAY_HW)
    cats = {'Entertainment': 25, 'Utilities': 20, 'Gaming': 15, 'E-commerce': 25, 'Gift Cards': 10, 'Education': 5}
    out = []
    for i in range(rint(1, 2)):
        m = fraud_online_merchant(cats, 0.4, 0.3)
        dev = rch(c.devices) if rng.random() < 0.45 else fraud_device()
        ip = 'India' if rng.random() < 0.6 else wc(FR_IP)
        entry = 'Online Authentication' if rng.random() < 0.6 else 'Manual Entry'
        out.append(ftx(c, t, 'Online', m.cat, m, round(unif(150, 2500), 2), dev, ip, entry, None, card))
        t = t + timedelta(hours=rint(5, 72))
    return out


def scen_G():   # skimmed / counterfeit POS in home area
    c = fcust()
    card = rch(c.cards)
    loc = c.home if rng.random() < 0.85 else india_loc(wchoice(IN_NAMES, IN_W))
    t = rand_time(DAY_HW)
    cats = {'Fuel': 25, 'Restaurants': 20, 'Grocery': 20, 'Fashion': 20, 'Electronics': 15}
    out = []
    for i in range(rint(1, 2)):
        cat = wc(cats)
        m = get_merchant(loc.country, loc.city, cat, new_p=0.3)
        amt = float(np.clip(c.avg_base * unif(0.7, 3), 150, 60000))
        entry = 'Swipe' if rng.random() < 0.75 else 'Chip'
        out.append(ftx(c, t, 'POS', cat, m, round(amt, 2), None, None, entry, rch(m.terms), card))
        t = t + timedelta(hours=rint(1, 48))
    return out


SCENARIOS = [('Card Testing Burst', 32, scen_A), ('International CNP', 28, scen_B),
             ('Account Takeover Online', 22, scen_C), ('Lost/Stolen Card POS Spree', 22, scen_D),
             ('ATM Cash-Out', 14, scen_E), ('Low-Value Online Fraud', 16, scen_F),
             ('Skimmed POS Home Area', 16, scen_G)]
for name, target, fn in SCENARIOS:
    got = 0
    while got < target:
        ev = fn()[:target - got]
        for x in ev:
            x['scen'] = name
        all_tx += ev
        got += len(ev)

assert len(all_tx) == N_UNIQUE, len(all_tx)

# ----------------------------------------------------------------- behaviour features
by_c = {}
for tx in all_tx:
    by_c.setdefault(tx['c'].id, []).append(tx)

for cid, L in by_c.items():
    L.sort(key=lambda x: x['t'])
    c = L[0]['c']
    known = set(c.base_devices)
    prev_geo = (c.home.lat, c.home.lon)
    for i, tx in enumerate(L):
        t = tx['t']
        c1 = c24 = n30 = 0
        s30 = 0.0
        for j in range(i - 1, -1, -1):
            dt = (t - L[j]['t']).total_seconds()
            if dt > 30 * 86400:
                break
            if dt <= 3600:
                c1 += 1
            if dt <= 86400:
                c24 += 1
            s30 += L[j]['amt']
            n30 += 1
        avg30 = s30 / n30 if n30 else c.avg_base * float(rng.lognormal(0, 0.15))
        tsl = rint(1500, 30000) if i == 0 else int((t - L[i - 1]['t']).total_seconds() // 60)
        d = haversine(prev_geo, tx['geo'])
        if d < 1:
            d = abs(float(rng.normal(3, 2)))
        newdev = False
        if tx['ch'] == 'Online':
            newdev = tx['device'] not in known
            known.add(tx['device'])
        prev_geo = tx['geo']
        tx['f'] = dict(c1=c1, c24=c24, avg30=avg30, tsl=tsl, dist=round(d, 1), newdev=newdev)
        tx['intl'] = tx['m'].country != 'India'

# ----------------------------------------------------------------- alerts, status, investigation, chargebacks
def sigmoid(x):
    return 1 / (1 + math.exp(-x))


def risk_logit(tx):
    f = tx['f']
    s = BASE_LOGIT
    ratio = tx['amt'] / max(f['avg30'], 1)
    if ratio > 3:
        s += 1.0
    if ratio > 6:
        s += 0.8
    if tx['amt'] >= 50000:
        s += 0.4
    if f['c1'] >= 3:
        s += 1.7
    elif f['c1'] == 2:
        s += 0.8
    if f['c24'] >= 6:
        s += 0.8
    if tx['intl']:
        s += 0.9
    if tx['ch'] == 'Online' and tx['ip'] != 'India':
        s += 0.8
    if tx['ch'] == 'Online' and tx['ip'] != tx['m'].country:
        s += 0.4
    if f['newdev']:
        s += 0.9
    if tx['m'].hr:
        s += 0.9
    if f['dist'] > 500 and f['tsl'] < 360:
        s += 1.8
    elif f['dist'] > 200 and f['tsl'] < 150:
        s += 1.0
    if tx['t'].hour <= 5:
        s += 0.5
    if tx['ch'] == 'ATM' and tx['intl']:
        s += 0.6
    if tx['amt'] <= 1500 and f['c1'] >= 2:
        s += 0.5
    if tx['label']:
        s += 1.5          # latent signals the bank sees that are not columns in this dataset
    return s + float(rng.normal(0, 0.6))


def cb_status(age, p_won):
    if age < 30:
        return wchoice(['Filed', 'Pending', 'Won', 'Lost'], [60, 36, 2, 2])
    if age < 90:
        return wchoice(['Filed', 'Pending', 'Won', 'Lost'], [14, 26, 60 * p_won, 60 * (1 - p_won)])
    return wchoice(['Filed', 'Pending', 'Won', 'Lost'], [1, 6, 93 * p_won, 93 * (1 - p_won)])


for tx in all_tx:
    tx['alert'] = bool(rng.random() < sigmoid(risk_logit(tx)))
    alert, fraud, online = tx['alert'], tx['label'] == 1, tx['ch'] == 'Online'
    if fraud:
        declined = rng.random() < (0.52 if alert else 0.10)
    else:
        declined = rng.random() < (0.12 if alert else 0.03)
    if not declined:
        tx['status'], tx['code'] = 'Approved', '00'
    else:
        tx['status'] = 'Declined'
        if fraud:
            tx['code'] = wchoice(['59', '05', '62', '57'], [60, 15, 10, 15]) if alert else \
                wchoice(['51', '61', '05', '14'], [40, 25, 25, 10])
        elif alert:
            tx['code'] = wchoice(['59', '05', '62'], [70, 20, 10])
        elif online:
            tx['code'] = wchoice(['51', '05', '61', '54', '91', '65', '82', '96'], [32, 22, 14, 5, 8, 7, 8, 4])
        else:
            tx['code'] = wchoice(['51', '05', '61', '54', '55', '91', '96'], [30, 20, 12, 4, 22, 8, 4])
    age = (SNAPSHOT - tx['t']).days
    approved = tx['status'] == 'Approved'
    tx['cb'], tx['inv'] = 'Not Applicable', 'Not Investigated'
    if fraud:
        tx['inv'] = 'Confirmed Fraud'
        if approved and tx['ch'] != 'ATM':
            p_init = 0.86 if online else 0.75
            if rng.random() < p_init:
                if tx['entry'] == 'Online Authentication':
                    pw = 0.45
                elif tx['ch'] == 'Online':
                    pw = 0.70
                elif tx['entry'] == 'Chip':
                    pw = 0.40
                else:
                    pw = 0.70
                tx['cb'] = cb_status(age, pw)
    else:
        if alert:
            p_ui = 0.30 if age < 21 else 0.03
            u = rng.random()
            tx['inv'] = 'Under Investigation' if u < p_ui else ('Not Investigated' if u < p_ui + 0.08 else 'Legitimate Transaction')
        if approved and rng.random() < (0.012 if alert else 0.005):      # customer dispute on a legitimate txn
            tx['cb'] = cb_status(age, 0.25)
            if tx['cb'] in ('Filed', 'Pending'):
                tx['inv'] = 'Under Investigation' if rng.random() < 0.7 else 'Legitimate Transaction'
            else:
                tx['inv'] = 'Legitimate Transaction'

# ----------------------------------------------------------------- assemble clean dataset
all_tx.sort(key=lambda x: (x['t'], x['c'].id))
COLS = ['Transaction_ID', 'Transaction_DateTime', 'Card_Token', 'Customer_ID', 'Account_ID', 'Transaction_Amount',
        'Currency', 'Merchant_ID', 'Merchant_Category', 'Merchant_Country', 'Merchant_City',
        'Transaction_Channel', 'Card_Present_Flag', 'Card_Entry_Mode', 'Terminal_ID', 'Device_ID',
        'IP_Country', 'Billing_Country', 'Domestic_International_Flag', 'Transaction_Status',
        'Authorization_Response_Code', 'Customer_Avg_Amount_30D', 'Transaction_Count_1H',
        'Transaction_Count_24H', 'Time_Since_Last_Transaction_Min', 'Distance_From_Previous_Transaction_KM',
        'High_Risk_Merchant_Flag', 'Alert_Flag', 'Confirmed_Fraud_Flag', 'Chargeback_Status',
        'Investigation_Outcome']
assert len(COLS) == 31
yn = lambda b: 'Yes' if b else 'No'
rows = []
for n, tx in enumerate(all_tx):
    m, f = tx['m'], tx['f']
    rows.append([
        f"TXN{100001 + n}", tx['t'].strftime('%Y-%m-%d %H:%M:%S'), tx['card'][0], tx['c'].id, tx['card'][1],
        tx['amt'], 'INR', m.id, m.cat, m.country, m.city, tx['ch'], yn(tx['ch'] != 'Online'), tx['entry'],
        tx['term'] if tx['term'] else '', tx['device'] if tx['device'] else '', tx['ip'] if tx['ip'] else '',
        'India', 'International' if tx['intl'] else 'Domestic', tx['status'], tx['code'],
        round(f['avg30'], 2), f['c1'], f['c24'], f['tsl'], f['dist'], yn(m.hr), yn(tx['alert']),
        yn(tx['label'] == 1), tx['cb'], tx['inv']])
clean = pd.DataFrame(rows, columns=COLS)
scen = pd.Series([tx['scen'] for tx in all_tx])

# ---- verification of business rules on the clean data
assert clean.Transaction_ID.is_unique and len(clean) == N_UNIQUE
assert (clean.Confirmed_Fraud_Flag == 'Yes').sum() == N_FRAUD
assert clean.Transaction_DateTime.min() >= '2026-05-01 00:00:00' and clean.Transaction_DateTime.max() <= '2026-10-31 23:59:59'
assert ((clean.Transaction_Channel == 'Online') == (clean.Card_Present_Flag == 'No')).all()
assert (clean.loc[clean.Transaction_Channel == 'Online', 'Terminal_ID'] == '').all()
assert (clean.loc[clean.Transaction_Channel != 'Online', 'Terminal_ID'] != '').all()
assert (clean.loc[clean.Transaction_Channel == 'Online', 'Device_ID'] != '').all()
assert (clean.Transaction_Count_24H >= clean.Transaction_Count_1H).all()
assert (clean[['Transaction_Count_1H', 'Time_Since_Last_Transaction_Min', 'Distance_From_Previous_Transaction_KM']] >= 0).all().all()
assert clean.Transaction_Amount.between(100, 200000).all()
assert (clean.loc[clean.Transaction_Status == 'Declined', 'Chargeback_Status'] == 'Not Applicable').all()
assert (clean.loc[clean.Confirmed_Fraud_Flag == 'Yes', 'Investigation_Outcome'] == 'Confirmed Fraud').all()
assert (clean.loc[clean.Confirmed_Fraud_Flag == 'No', 'Investigation_Outcome'] != 'Confirmed Fraud').all()
assert ((clean.Merchant_Country != 'India') == (clean.Domestic_International_Flag == 'International')).all()

# ---- diagnostics for calibration (printed only; not part of deliverables)
fr = clean.Confirmed_Fraud_Flag == 'Yes'
print("DIAG legit alert rate %.3f | fraud alert rate %.3f | fraud declined share %.3f | legit declined %.3f" % (
    (clean[~fr].Alert_Flag == 'Yes').mean(), (clean[fr].Alert_Flag == 'Yes').mean(),
    (clean[fr].Transaction_Status == 'Declined').mean(), (clean[~fr].Transaction_Status == 'Declined').mean()))
print("DIAG customers %d, with fraud %d | merchants %d | intl share %.3f" % (
    clean.Customer_ID.nunique(), clean[fr].Customer_ID.nunique(), clean.Merchant_ID.nunique(),
    (clean.Domestic_International_Flag == 'International').mean()))
print("DIAG channel", clean.Transaction_Channel.value_counts().to_dict())
print("DIAG chargeback", clean.Chargeback_Status.value_counts().to_dict())
print("DIAG investigation", clean.Investigation_Outcome.value_counts().to_dict())
print("DIAG scenario", scen[fr.values].value_counts().to_dict())
print("DIAG fraud alerts by scen", pd.crosstab(scen[fr.values].values, clean[fr].Alert_Flag.values).to_dict())

# ----------------------------------------------------------------- string-formatted version
fmt = clean.copy()
fmt['Transaction_Amount'] = clean['Transaction_Amount'].map('{:.2f}'.format)
fmt['Customer_Avg_Amount_30D'] = clean['Customer_Avg_Amount_30D'].map('{:.2f}'.format)
fmt['Distance_From_Previous_Transaction_KM'] = clean['Distance_From_Previous_Transaction_KM'].map('{:.1f}'.format)
for col in ['Transaction_Count_1H', 'Transaction_Count_24H', 'Time_Since_Last_Transaction_Min']:
    fmt[col] = clean[col].astype(int).astype(str)
fmt = fmt.astype(str)
fmt.to_csv(f"{OUT}/credit_card_transactions_clean_reference.csv", index=False, encoding='utf-8-sig')

# ----------------------------------------------------------------- intentional data-quality issues
dirty = fmt.copy()
log = []
fraud_mask = (clean.Confirmed_Fraud_Flag == 'Yes').values
online_mask = (clean.Transaction_Channel == 'Online').values
used = set()


def pick(n, mask=None):
    p = [i for i in range(len(clean)) if not fraud_mask[i] and i not in used and (mask is None or mask[i])]
    sel = [int(x) for x in rng.choice(p, n, replace=False)]
    used.update(sel)
    return sel


def setv(i, col, new, issue):
    old = dirty.at[i, col]
    dirty.at[i, col] = new
    log.append(dict(idx=i, Transaction_ID=clean.at[i, 'Transaction_ID'], Column_Affected=col, Issue_Type=issue,
                    Original_Value=old if old != '' else '<BLANK>',
                    Corrupted_Value=new if new != '' else '<BLANK>'))


# 1. Missing values
for i in pick(15):
    setv(i, 'Merchant_ID', '', 'Missing Value')
for i in pick(20, online_mask):
    setv(i, 'Device_ID', '', 'Missing Value')
for i in pick(15):
    setv(i, 'Merchant_City', '', 'Missing Value')
for i in pick(15, online_mask):
    setv(i, 'IP_Country', '', 'Missing Value')
for i in pick(15):
    setv(i, 'Customer_Avg_Amount_30D', '', 'Missing Value')
for i in pick(15, ~online_mask):
    setv(i, 'Terminal_ID', '', 'Missing Value')

# 2. Incorrect data types (numbers stored as text)
for i in pick(15):
    v = clean.at[i, 'Transaction_Amount']
    setv(i, 'Transaction_Amount', rch([f"₹{v:,.2f}", f"Rs. {v:.2f}", f"{v:.2f} INR"]), 'Incorrect Data Type')
words = {0: 'zero', 1: 'one', 2: 'two', 3: 'three', 4: 'four', 5: 'five', 6: 'six', 7: 'seven', 8: 'eight', 9: 'nine'}
for i in pick(8, (clean.Transaction_Count_24H <= 9).values):
    setv(i, 'Transaction_Count_24H', words[int(clean.at[i, 'Transaction_Count_24H'])], 'Incorrect Data Type')
for i in pick(12):
    setv(i, 'Distance_From_Previous_Transaction_KM', f"{clean.at[i, 'Distance_From_Previous_Transaction_KM']:.1f} km",
         'Incorrect Data Type')

# 3. Invalid transaction amounts
for i in pick(8):
    setv(i, 'Transaction_Amount', '-' + dirty.at[i, 'Transaction_Amount'], 'Invalid Amount (Negative)')
for i in pick(6):
    setv(i, 'Transaction_Amount', '0.00', 'Invalid Amount (Zero)')
for i in pick(6):
    setv(i, 'Transaction_Amount', rch(['9999999.00', '1250000.00', '5000000.00']), 'Invalid Amount (Outlier > 200,000)')
for i in pick(5):
    setv(i, 'Transaction_Amount', 'N/A', 'Invalid Amount (Non-numeric)')

# 4. Channel spelling / capitalisation
CH_VAR = {'Online': ['online', 'ONLINE', 'Onlin', 'Online '], 'POS': ['pos', 'Pos', 'P.O.S', 'POS '],
          'ATM': ['atm', 'Atm', 'ATM ', 'A.T.M']}
for i in pick(35):
    setv(i, 'Transaction_Channel', rch(CH_VAR[clean.at[i, 'Transaction_Channel']]), 'Inconsistent Channel Spelling/Case')

# 5. Missing / badly formatted dates
for i in pick(10):
    d = datetime.strptime(clean.at[i, 'Transaction_DateTime'], '%Y-%m-%d %H:%M:%S')
    setv(i, 'Transaction_DateTime', d.strftime('%d/%m/%Y %H:%M'), 'Date Format Inconsistency (DD/MM/YYYY)')
for i in pick(6):
    d = datetime.strptime(clean.at[i, 'Transaction_DateTime'], '%Y-%m-%d %H:%M:%S')
    setv(i, 'Transaction_DateTime', d.strftime('%d-%b-%Y'), 'Date Format Inconsistency (time missing)')
for i in pick(4):
    d = datetime.strptime(clean.at[i, 'Transaction_DateTime'], '%Y-%m-%d %H:%M:%S')
    setv(i, 'Transaction_DateTime', d.strftime('%d-%m-%y %H:%M'), 'Date Format Inconsistency (2-digit year)')
for i in pick(6):
    setv(i, 'Transaction_DateTime', '', 'Missing Value')
for i in pick(4):
    tm = clean.at[i, 'Transaction_DateTime'][11:]
    setv(i, 'Transaction_DateTime', rch(['2026-02-30 ', '2026-13-05 ', '2026-10-32 ', '2026-00-15 ']) + tm,
         'Impossible Date')

# 6. Inconsistent country names
CVAR = {'India': ['IN', 'india', 'INDIA', 'India ', 'Ind'],
        'United States': ['USA', 'US', 'United States of America', 'U.S.A.'],
        'United Kingdom': ['UK', 'U.K.', 'Great Britain'], 'United Arab Emirates': ['UAE', 'U.A.E.'],
        'Singapore': ['SG', 'SINGAPORE'], 'Thailand': ['THAILAND', 'Thai']}
for i in pick(30):
    cols = ['Merchant_Country', 'Billing_Country'] + (['IP_Country'] if online_mask[i] and dirty.at[i, 'IP_Country'] != '' else [])
    col = rch(cols)
    v = dirty.at[i, col]
    setv(i, col, rch(CVAR[v]) if v in CVAR else v.upper(), 'Inconsistent Country Name')

# 7. Wrong Card_Present_Flag
for i in pick(15):
    setv(i, 'Card_Present_Flag', 'Yes' if dirty.at[i, 'Card_Present_Flag'] == 'No' else 'No', 'Incorrect Card_Present_Flag')

# 8. Inconsistent transaction status
ST_VAR = {'Approved': ['APPROVED', 'approved', 'Approve', 'Success'], 'Declined': ['DECLINED', 'declined', 'Decline', 'Failed']}
for i in pick(17):
    setv(i, 'Transaction_Status', rch(ST_VAR[clean.at[i, 'Transaction_Status']]), 'Inconsistent Status Label')
dec_mask = (clean.Transaction_Status == 'Declined').values
for i in pick(4, dec_mask):
    setv(i, 'Transaction_Status', 'Approved', 'Status Conflicts With Response Code')
for i in pick(4, ~dec_mask):
    setv(i, 'Transaction_Status', 'Declined', 'Status Conflicts With Response Code')

# 9. Duplicate records (exact copies, placed after the original)
dup_src = pick(N_DUP)
order = [(float(i), i, False) for i in range(len(dirty))]
order += [(i + float(rng.uniform(0.5, 60)), i, True) for i in dup_src]
order.sort(key=lambda x: x[0])
final = dirty.iloc[[o[1] for o in order]].reset_index(drop=True)
pos_orig, pos_dup = {}, {}
for p, (_, i, is_dup) in enumerate(order):
    (pos_dup if is_dup else pos_orig)[i] = p + 2          # Excel row number (header = row 1)
for i in dup_src:
    log.append(dict(idx=i, Transaction_ID=clean.at[i, 'Transaction_ID'], Column_Affected='(entire row)',
                    Issue_Type='Duplicate Record', Original_Value=f"Original at Excel row {pos_orig[i]}",
                    Corrupted_Value=f"Exact copy at Excel row {pos_dup[i]}"))
assert len(final) == TOTAL_ROWS and list(final.columns) == COLS

lg = pd.DataFrame(log)
lg['Excel_Row_Number'] = [pos_dup[r.idx] if r.Issue_Type == 'Duplicate Record' else pos_orig[r.idx] for r in lg.itertuples()]
lg = lg.sort_values('Excel_Row_Number').reset_index(drop=True)
lg.insert(0, 'Issue_ID', [f"DQ{n + 1:04d}" for n in range(len(lg))])
lg = lg[['Issue_ID', 'Transaction_ID', 'Excel_Row_Number', 'Column_Affected', 'Issue_Type', 'Original_Value', 'Corrupted_Value']]

final.to_csv(f"{OUT}/credit_card_transactions_synthetic.csv", index=False, encoding='utf-8-sig')
lg.to_csv(f"{OUT}/data_quality_issue_log.csv", index=False, encoding='utf-8-sig')

# ----------------------------------------------------------------- DQ summary (markdown)
g = lg.groupby('Issue_Type').agg(Records=('Issue_ID', 'count'),
                                 Columns=('Column_Affected', lambda s: ', '.join(sorted(set(s))))).reset_index()
affected_rows = lg.Excel_Row_Number.nunique()
md = ["# Data Quality Issue Summary", "",
      "All issues were injected programmatically into `credit_card_transactions_synthetic.csv`. "
      "The untouched generated data is preserved in `credit_card_transactions_clean_reference.csv` "
      "(answer key - open it only after you finish your own cleaning). Every injected issue is listed "
      "row-by-row in `data_quality_issue_log.csv`.", "",
      f"- Rows in main CSV: **{len(final):,}** (includes {N_DUP} duplicate rows, so {N_UNIQUE:,} unique transactions)",
      f"- Rows affected by at least one injected issue: **{affected_rows}** "
      f"({affected_rows / len(final) * 100:.1f}% of rows; each issue was placed on a different row)",
      "- `Transaction_ID` and `Confirmed_Fraud_Flag` were deliberately left untouched, and no confirmed-fraud row was corrupted.",
      "", "| Issue type | Records affected | Column(s) |", "|---|---:|---|"]
for r in g.itertuples():
    md.append(f"| {r.Issue_Type} | {r.Records} | {r.Columns} |")
md += ["", "## Notes on blanks that are NOT errors", "",
       "- `Terminal_ID` is blank by design for Online transactions; `Device_ID` and `IP_Country` are blank by design for POS/ATM transactions.",
       "- Injected missing values are the blanks that appear where the channel says a value should exist "
       "(e.g. an Online row with no `Device_ID`, or a POS row with no `Terminal_ID`).",
       "", "## Other things to check (not counted above)", "",
       "- `Authorization_Response_Code` is stored as text (e.g. `00`, `05`); Excel may drop the leading zero on open.",
       "- `Customer_Avg_Amount_30D`, `Transaction_Count_*`, `Time_Since_Last_Transaction_Min` and `Distance_...` are computed from the generated history; see the methodology file for how first-in-dataset transactions were handled."]
open(f"{OUT}/data_quality_issue_summary.md", "w", encoding="utf-8").write("\n".join(md))
print(g.to_string(index=False))
print("AFFECTED ROWS", affected_rows, "TOTAL", len(final))

# ----------------------------------------------------------------- data dictionary
DD = [
 ("Transaction_ID", "Text", "Transaction Information", "Unique transaction identifier (unique in the clean dataset; duplicated only in the injected duplicate rows).", "TXN + 6 digits, e.g. TXN100001", "Assigned in chronological order."),
 ("Transaction_DateTime", "Datetime (text)", "Transaction Information", "Date and time the transaction was made.", "YYYY-MM-DD HH:MM:SS; 2026-05-01 to 2026-10-31", "Intentional date errors exist."),
 ("Card_Token", "Text", "Transaction Information", "Masked / tokenised card identifier. Not a real card number.", "TKN + 12 hex characters", "1-3 cards per customer."),
 ("Customer_ID", "Text", "Transaction Information", "Customer identifier. Customers recur across many transactions.", "CUST + 5 digits", "650 customers."),
 ("Account_ID", "Text", "Transaction Information", "Bank account linked to the card.", "ACC + 10 digits", "A customer can have 1-2 accounts."),
 ("Transaction_Amount", "Numeric (INR)", "Transaction Information", "Transaction amount in rupees (foreign spend already converted to INR).", "100.00 - 200000.00 in clean data", "Intentional invalid / text amounts exist."),
 ("Currency", "Text", "Transaction Information", "Currency of the amount.", "INR", "INR throughout."),
 ("Merchant_ID", "Text", "Merchant Information", "Merchant identifier.", "MER + 6 digits", "ATM rows carry the ATM operator ID."),
 ("Merchant_Category", "Text", "Merchant Information", "Merchant business category.", "Grocery, Fuel, Electronics, Restaurants, Travel, E-commerce, Healthcare, Entertainment, Jewellery, ATM, Fashion, Utilities, Education, Gaming, Gift Cards, Money Transfer", ""),
 ("Merchant_Country", "Text", "Merchant Information", "Country where the merchant is located.", "India plus selected international countries", "Inconsistent spellings injected in some rows."),
 ("Merchant_City", "Text", "Merchant Information", "City of the merchant, consistent with Merchant_Country.", "Realistic city names", "Online merchants use head-office city."),
 ("Transaction_Channel", "Text", "Channel & Device", "How the transaction was made.", "Online, POS, ATM", "Spelling/case issues injected."),
 ("Card_Present_Flag", "Text", "Channel & Device", "Whether the physical card was present.", "Yes / No", "Online = No; POS and ATM = Yes in clean data."),
 ("Card_Entry_Mode", "Text", "Channel & Device", "How card details were captured.", "Chip, Contactless, Swipe, Manual Entry, Online Authentication, ATM PIN", "Contactless only below INR 5,000."),
 ("Terminal_ID", "Text", "Channel & Device", "POS / ATM terminal identifier.", "TRM + 6 digits", "Blank by design for Online."),
 ("Device_ID", "Text", "Channel & Device", "Device identifier for online transactions.", "DEV + 8 hex characters", "Blank by design for POS/ATM."),
 ("IP_Country", "Text", "Location & Risk", "Country of the IP address used for online transactions.", "Country name", "Blank by design for POS/ATM."),
 ("Billing_Country", "Text", "Location & Risk", "Customer billing country.", "India", "All customers are India-billed."),
 ("Domestic_International_Flag", "Text", "Location & Risk", "Domestic if Merchant_Country equals Billing_Country, otherwise International.", "Domestic / International", ""),
 ("Transaction_Status", "Text", "Location & Risk", "Authorization decision.", "Approved / Declined", "Label inconsistencies injected."),
 ("Authorization_Response_Code", "Text", "Location & Risk", "ISO 8583-style response code.", "00 Approved; 05 Do not honor; 14 Invalid card number; 51 Insufficient funds; 54 Expired card; 55 Incorrect PIN; 57 Txn not permitted; 59 Suspected fraud; 61 Exceeds limit; 62 Restricted card; 65 Activity count exceeded; 82 CVV check failed; 91 Issuer unavailable; 96 System error", "Stored as text."),
 ("Customer_Avg_Amount_30D", "Numeric (INR)", "Spending Behaviour", "Average amount of the customer's previous transactions in the 30 days before this one (all attempts, approved and declined). If no prior transaction in the window, the customer's baseline average is used.", "Decimal, 2 places", "Uses past data only."),
 ("Transaction_Count_1H", "Integer", "Spending Behaviour", "Number of the customer's transactions in the hour before this one (excludes this one).", ">= 0", "Counts attempts incl. declined."),
 ("Transaction_Count_24H", "Integer", "Spending Behaviour", "Number of the customer's transactions in the 24 hours before this one (excludes this one).", ">= Transaction_Count_1H", ""),
 ("Time_Since_Last_Transaction_Min", "Integer", "Spending Behaviour", "Minutes since the customer's previous transaction. For a customer's first transaction in the dataset a simulated pre-period gap is used.", ">= 0", ""),
 ("Distance_From_Previous_Transaction_KM", "Numeric", "Spending Behaviour", "Approximate straight-line distance between this transaction's location and the previous one. Online uses the IP location; POS/ATM use the merchant city.", ">= 0, 1 decimal", ""),
 ("High_Risk_Merchant_Flag", "Text", "Fraud & Investigation", "Merchant is on the bank's high-risk watch list (property of the merchant).", "Yes / No", "Same merchant always has the same value."),
 ("Alert_Flag", "Text", "Fraud & Investigation", "Bank monitoring system flagged the transaction as suspicious at authorization time.", "Yes / No", "Alert time is not a separate column; it is the transaction time."),
 ("Confirmed_Fraud_Flag", "Text", "Fraud & Investigation", "Fraud confirmed after investigation or customer dispute (includes confirmed fraud attempts that were declined).", "Yes / No", "Target label; about 1.5%."),
 ("Chargeback_Status", "Text", "Fraud & Investigation", "State of any chargeback on the transaction. Filed = raised, no merchant response yet; Pending = in representment/review; Won/Lost = resolved.", "Filed, Pending, Won, Lost, Not Applicable", "Not every fraud is charged back."),
 ("Investigation_Outcome", "Text", "Fraud & Investigation", "Result of the bank's investigation (separate from the alert and from the chargeback).", "Confirmed Fraud, Legitimate Transaction, Under Investigation, Not Investigated", "Under Investigation rows are unresolved, so Confirmed_Fraud_Flag = No."),
]
pd.DataFrame(DD, columns=["Column_No_Name", "Data_Type", "Category", "Description", "Allowed_Values_Or_Format", "Notes"]) \
    .rename(columns={"Column_No_Name": "Column_Name"}) \
    .insert(0, "Column_No", list(range(1, 32))) if False else None
dd = pd.DataFrame(DD, columns=["Column_Name", "Data_Type", "Category", "Description", "Allowed_Values_Or_Format", "Notes"])
dd.insert(0, "Column_No", range(1, 32))
assert list(dd.Column_Name) == COLS
dd.to_csv(f"{OUT}/data_dictionary.csv", index=False, encoding='utf-8-sig')
print("DONE")
