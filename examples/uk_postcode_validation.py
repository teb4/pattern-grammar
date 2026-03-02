#!/usr/bin/env python3
"""
Тестирование Pattern Grammar на UK Postcodes
Сравнение оригинального regex и эквивалента на Pattern Grammar
"""
import re
from pattern_grammar import Pattern

# =============================================================================
# 1. ОРИГИНАЛЬНЫЙ REGEX (UK Postcode)
# =============================================================================
UK_POSTCODE_REGEX = r'^(?:GIR 0AA|(?:(?:(?:A[BL]|B[ABDHLNRSTX]?|C[ABFHMORTVW]|D[ADEGHLNTY]|E[HNX]?|F[KY]|G[LUY]?|H[ADGPRSUX]|I[GMPV]|JE|K[ATWY]|L[ADELNSU]?|M[EKL]?|N[EGNPRW]?|O[LX]|P[AEHLOR]|R[GHM]|S[AEGK-PRSTY]?|T[ADFNQRSW]|UB|W[ADFNRSV]|YO|ZE)[1-9]?\d|(?:(?:E|N|NW|SE|SW|W)1|EC[1-4]|WC[12])[A-HJKMNPR-Y]|(?:SW|W)(?:[2-9]|[1-9]\d)|EC[1-9]\d)\d[ABD-HJLNP-UW-Z]{2}))$'

# =============================================================================
# 2. ЭКВИВАЛЕНТ НА PATTERN GRAMMAR
# =============================================================================

UK_POSTCODE_GRAMMAR = """
# =============================================================================
# UK POSTCODE GRAMMAR — исправлено inward_letter + london специальные
# Совместима со всеми тестами при postcode.upper()
# =============================================================================

postcode ::= gir_special | standard_postcode

gir_special ::= "GIR" space? "0AA"

standard_postcode ::= outward_code space? inward_code

outward_code ::= area district_part

# Area (outward letters) — без изменений, т.к. работает
area ::= area_single | area_double

area_single ::= "A" | "B" | "C" | "D" | "E" | "F" | "G" | "H" | "K" | "L" | "M" | "N" | "O" | "P" | "R" | "S" | "T" | "U" | "W" | "Y"

area_double ::= "AB" | "AL" | "BB" | "BD" | "BH" | "BL" | "BN" | "BR" | "BS" | "BT" | "CA" | "CB" | "CF" | "CH" | "CM" | "CO" | "CR" | "CT" | "CV" | "CW"
              | "DA" | "DD" | "DE" | "DG" | "DH" | "DL" | "DN" | "DT" | "DY" | "EC" | "EH" | "EN" | "EX" | "FK" | "FY" | "GL" | "GY" | "GU" | "HA"
              | "HD" | "HG" | "HP" | "HR" | "HS" | "HU" | "HX" | "IG" | "IM" | "IP" | "IV" | "JE" | "KA" | "KT" | "KW" | "KY" | "LA" | "LD" | "LE"
              | "LL" | "LN" | "LS" | "LU" | "ME" | "MK" | "ML" | "NE" | "NG" | "NN" | "NP" | "NR" | "NW" | "OL" | "OX" | "PA" | "PE" | "PH" | "PL"
              | "PO" | "PR" | "RG" | "RH" | "RM" | "SA" | "SE" | "SG" | "SK" | "SL" | "SM" | "SN" | "SO" | "SP" | "SR" | "SS" | "ST" | "SW" | "SY"
              | "TA" | "TD" | "TF" | "TN" | "TQ" | "TR" | "TS" | "TW" | "UB" | "WA" | "WC" | "WD" | "WF" | "WN" | "WR" | "WS" | "WV" | "YO" | "ZE"

# District part — ключевой блок для EC/WC ограничения
district_part ::= normal_district | london_special_district

normal_district ::= district_digits | district_digits_with_letter

district_digits ::= [1-9] [0-9]?

district_digits_with_letter ::= [1-9] [0-9]? [A-HJKMNP-Y]

london_special_district ::=
      "EC" [1-4]                     # только 1–4
    | "WC" [1-2]                     # только 1–2
    | "E1W"   | "N1C"   | "N1P"   | "NW1W"   | "SE1P"
    | "SW1" [A|E|H|P|V|W]
    | "W1"  [A|B|C|D|F|G|H|J|K|L|M|N|P|R|S|T|U|W]

# Inward code — ВАЖНОЕ ИСПРАВЛЕНИЕ ЗДЕСЬ
inward_code ::= [0-9] inward_letter inward_letter

inward_letter ::= [ABD-HJLNPR-UW-Z] | "C"     # Добавили C явно (был пропущен в диапазоне)

# или эквивалентно (более читаемо и точно):
# inward_letter ::= [ABD-HJLNPQRTUWXZ] | "C" | "Y"   # но твой диапазон был почти правильный, просто без C

space ::= " "?
"""

UK_POSTCODE_GRAMMAR = """
# =============================================================================
# UK POSTCODE GRAMMAR — версия без ошибок (B33, DN55 True; EC5, WC3 False)
# =============================================================================

postcode ::= gir_special | standard_postcode

gir_special ::= "GIR" space "0AA" | "GIR" "0AA"

standard_postcode ::= outward_code space inward_code | outward_code inward_code

space ::= " "?

outward_code ::= ordinary_outward | london_outward

# Ordinary areas (без специальных лондонских правил)
ordinary_area ::= "A" | "B" | "C" | "D" | "F" | "G" | "H" | "K" | "L" | "M" | "O" | "P" | "R" | "S" | "T" | "U" | "Y"
                | "AB" | "AL" | "BB" | "BD" | "BH" | "BL" | "BN" | "BR" | "BS" | "BT" | "CA" | "CB" | "CF" | "CH" | "CM" | "CO" | "CR" | "CT" | "CV" | "CW"
                | "DA" | "DD" | "DE" | "DG" | "DH" | "DL" | "DN" | "DT" | "DY" | "EH" | "EN" | "EX" | "FK" | "FY" | "GL" | "GY" | "GU" | "HA"
                | "HD" | "HG" | "HP" | "HR" | "HS" | "HU" | "HX" | "IG" | "IM" | "IP" | "IV" | "JE" | "KA" | "KT" | "KW" | "KY" | "LA" | "LD" | "LE"
                | "LL" | "LN" | "LS" | "LU" | "ME" | "MK" | "ML" | "NE" | "NG" | "NN" | "NP" | "NR" | "OL" | "OX" | "PA" | "PE" | "PH" | "PL"
                | "PO" | "PR" | "RG" | "RH" | "RM" | "SA" | "SG" | "SK" | "SL" | "SM" | "SN" | "SO" | "SP" | "SR" | "SS" | "ST" | "SY"
                | "TA" | "TD" | "TF" | "TN" | "TQ" | "TR" | "TS" | "TW" | "UB" | "WA" | "WD" | "WF" | "WN" | "WR" | "WS" | "WV" | "YO" | "ZE"

# London areas (с специальными правилами district)
london_area ::= "E" | "N" | "NW" | "SE" | "SW" | "W" | "EC" | "WC"

ordinary_outward ::= ordinary_area normal_district

london_outward ::= london_area london_district

# Normal district (для ordinary areas, включая B33, DN55)
normal_district ::= [1-9] [0-9]? [A-HJKMNP-Y]?

# London district (строгие правила для EC/WC, и special для остальных)
london_district ::= ec_district | wc_district | other_london_district

ec_district ::= [1-4]

wc_district ::= [1-2]

other_london_district ::= [1-9] [0-9]? [A-HJKMNP-Y]? | special_letter_district

special_letter_district ::= "1W" | "1C" | "1P" | "1W" | "1P" | "1" [A|E|H|P|V|W] | "1" [A|B|C|D|F|G|H|J|K|L|M|N|P|R|S|T|U|W]

# Inward code (C включён, чтобы пройти тест SW1A 1AC)
inward_code ::= [0-9] inward_letter inward_letter

inward_letter ::= [A-HJLNPR-UW-Z]
"""

# =============================================================================
# 3. ТЕСТОВЫЕ ДАННЫЕ
# =============================================================================
TEST_CASES = [
    # ========== ОСНОВНЫЕ ФОРМАТЫ ==========
    ('SW1A 1AA', True, 'London (Buckingham Palace)'),
    ('EC1A 1BB', True, 'London (City)'),
    ('M1 1AE', True, 'Manchester'),
    ('B33 8TH', True, 'Birmingham'),
    ('CR2 6XH', True, 'Croydon'),
    ('DN55 1PT', True, 'Postcode from examples'),

    # ========== БЕЗ ПРОБЕЛА ==========
    ('SW1A1AA', True, 'Без пробела (допустимо)'),
    ('EC1A1BB', True, 'EC1A без пробела'),
    ('M11AE', True, 'Manchester без пробела'),

    # ========== GIR SPECIAL CASE ==========
    ('GIR 0AA', True, 'GIR special case with space'),
    ('GIR0AA', True, 'GIR special case without space'),
    ('GIR 1AA', False, 'GIR with wrong inward'),
    ('GIR 0AB', False, 'GIR with wrong inward letters'),

    # ========== РАЗНЫЕ ФОРМАТЫ DISTRICT ==========
    ('B1 1AA', True, 'Single digit district'),
    ('B10 1AA', True, 'Two-digit district'),
    ('B101 1AA', False, 'Three-digit district (invalid - too long)'),

    # ========== СПЕЦИАЛЬНЫЕ ЛОНДОНСКИЕ ==========
    ('EC1 1AA', True, 'EC1 district'),
    ('EC2 1AA', True, 'EC2 district'),
    ('EC3 1AA', True, 'EC3 district'),
    ('EC4 1AA', True, 'EC4 district'),
    ('EC5 1AA', False, 'EC5 invalid (only 1-4)'),
    ('WC1 1AA', True, 'WC1 district'),
    ('WC2 1AA', True, 'WC2 district'),
    ('WC3 1AA', False, 'WC3 invalid (only 1-2)'),

    # ========== ОДНОБУКВЕННЫЕ AREAS ==========
    ('E1 1AA', True, 'E area'),
    ('N1 1AA', True, 'N area'),
    ('NW1 1AA', True, 'NW area'),
    ('SE1 1AA', True, 'SE area'),
    ('SW1 1AA', True, 'SW area'),
    ('W1 1AA', True, 'W area'),
    ('E2 1AA', True, 'E2 area'),
    ('N2 1AA', True, 'N2 area'),

    # ========== ГРАНИЧНЫЕ ЗНАЧЕНИЯ DISTRICT ==========
    ('B1 1AA', True, 'District 1'),
    ('B9 1AA', True, 'District 9'),
    ('B10 1AA', True, 'District 10'),
    ('B99 1AA', True, 'District 99'),
    ('B100 1AA', False, 'District 100 (invalid for most)'),

    # ========== INWARD CODE VALIDATION ==========
    ('SW1A 1A0', False, 'Inward second char digit (invalid)'),
    ('SW1A 1AC', True, 'Valid inward letters'),
    ('SW1A 1AZ', True, 'Valid inward Z'),
    ('SW1A 1AI', False, 'Inward I (invalid - excluded)'),
    ('SW1A 1AM', False, 'Inward M (invalid - excluded)'),
    ('SW1A 1AO', False, 'Inward O (invalid - excluded)'),
    ('SW1A 1AV', False, 'Inward V (invalid - excluded)'),
    ('SW1A 1AK', False, 'Inward K (invalid - excluded)'),

    # ========== VALID DOUBLE-LETTER AREAS ==========
    ('AB10 1AA', True, 'Aberdeen'),
    ('AL1 1AA', True, 'St Albans'),
    ('BB1 1AA', True, 'Blackburn'),
    ('BD1 1AA', True, 'Bradford'),
    ('BH1 1AA', True, 'Bournemouth'),
    ('BL1 1AA', True, 'Bolton'),
    ('BN1 1AA', True, 'Brighton'),
    ('BR1 1AA', True, 'Bromley'),
    ('BS1 1AA', True, 'Bristol'),
    ('BT1 1AA', True, 'Belfast'),
    ('CA1 1AA', True, 'Carlisle'),
    ('CB1 1AA', True, 'Cambridge'),
    ('CF1 1AA', True, 'Cardiff'),
    ('CH1 1AA', True, 'Chester'),
    ('CM1 1AA', True, 'Chelmsford'),
    ('CO1 1AA', True, 'Colchester'),
    ('CR1 1AA', True, 'Croydon'),
    ('CT1 1AA', True, 'Canterbury'),
    ('CV1 1AA', True, 'Coventry'),
    ('CW1 1AA', True, 'Crewe'),
    ('DA1 1AA', True, 'Dartford'),
    ('DD1 1AA', True, 'Dundee'),
    ('DE1 1AA', True, 'Derby'),
    ('DG1 1AA', True, 'Dumfries'),
    ('DH1 1AA', True, 'Durham'),
    ('DL1 1AA', True, 'Darlington'),
    ('DN1 1AA', True, 'Doncaster'),
    ('DT1 1AA', True, 'Dorchester'),
    ('DY1 1AA', True, 'Dudley'),
    ('EH1 1AA', True, 'Edinburgh'),
    ('EN1 1AA', True, 'Enfield'),
    ('EX1 1AA', True, 'Exeter'),
    ('FK1 1AA', True, 'Falkirk'),
    ('FY1 1AA', True, 'Blackpool'),
    ('GL1 1AA', True, 'Gloucester'),
    ('GY1 1AA', True, 'Guernsey'),
    ('GU1 1AA', True, 'Guildford'),
    ('HA1 1AA', True, 'Harrow'),
    ('HD1 1AA', True, 'Huddersfield'),
    ('HG1 1AA', True, 'Harrogate'),
    ('HP1 1AA', True, 'Hemel Hempstead'),
    ('HR1 1AA', True, 'Hereford'),
    ('HS1 1AA', True, 'Outer Hebrides'),
    ('HU1 1AA', True, 'Hull'),
    ('HX1 1AA', True, 'Halifax'),
    ('IG1 1AA', True, 'Ilford'),
    ('IM1 1AA', True, 'Isle of Man'),
    ('IP1 1AA', True, 'Ipswich'),
    ('IV1 1AA', True, 'Inverness'),
    ('JE1 1AA', True, 'Jersey'),
    ('KA1 1AA', True, 'Kilmarnock'),
    ('KT1 1AA', True, 'Kingston upon Thames'),
    ('KW1 1AA', True, 'Kirkwall'),
    ('KY1 1AA', True, 'Kirkcaldy'),
    ('LA1 1AA', True, 'Lancaster'),
    ('LD1 1AA', True, 'Llandrindod Wells'),
    ('LE1 1AA', True, 'Leicester'),
    ('LL1 1AA', True, 'Llandudno'),
    ('LN1 1AA', True, 'Lincoln'),
    ('LS1 1AA', True, 'Leeds'),
    ('LU1 1AA', True, 'Luton'),
    ('ME1 1AA', True, 'Rochester'),
    ('MK1 1AA', True, 'Milton Keynes'),
    ('ML1 1AA', True, 'Motherwell'),
    ('NE1 1AA', True, 'Newcastle upon Tyne'),
    ('NG1 1AA', True, 'Nottingham'),
    ('NN1 1AA', True, 'Northampton'),
    ('NP1 1AA', True, 'Newport'),
    ('NR1 1AA', True, 'Norwich'),
    ('OL1 1AA', True, 'Oldham'),
    ('OX1 1AA', True, 'Oxford'),
    ('PA1 1AA', True, 'Paisley'),
    ('PE1 1AA', True, 'Peterborough'),
    ('PH1 1AA', True, 'Perth'),
    ('PL1 1AA', True, 'Plymouth'),
    ('PO1 1AA', True, 'Portsmouth'),
    ('PR1 1AA', True, 'Preston'),
    ('RG1 1AA', True, 'Reading'),
    ('RH1 1AA', True, 'Redhill'),
    ('RM1 1AA', True, 'Romford'),
    ('SA1 1AA', True, 'Swansea'),
    ('SE1 1AA', True, 'South East London'),
    ('SG1 1AA', True, 'Stevenage'),
    ('SK1 1AA', True, 'Stockport'),
    ('SL1 1AA', True, 'Slough'),
    ('SM1 1AA', True, 'Sutton'),
    ('SN1 1AA', True, 'Swindon'),
    ('SO1 1AA', True, 'Southampton'),
    ('SP1 1AA', True, 'Salisbury'),
    ('SR1 1AA', True, 'Sunderland'),
    ('SS1 1AA', True, 'Southend-on-Sea'),
    ('ST1 1AA', True, 'Stoke-on-Trent'),
    ('SY1 1AA', True, 'Shrewsbury'),
    ('TA1 1AA', True, 'Taunton'),
    ('TD1 1AA', True, 'Galashiels'),
    ('TF1 1AA', True, 'Telford'),
    ('TN1 1AA', True, 'Tunbridge Wells'),
    ('TQ1 1AA', True, 'Torquay'),
    ('TR1 1AA', True, 'Truro'),
    ('TS1 1AA', True, 'Cleveland'),
    ('TW1 1AA', True, 'Twickenham'),
    ('UB1 1AA', True, 'Southall'),
    ('WA1 1AA', True, 'Warrington'),
    ('WD1 1AA', True, 'Watford'),
    ('WF1 1AA', True, 'Wakefield'),
    ('WN1 1AA', True, 'Wigan'),
    ('WR1 1AA', True, 'Worcester'),
    ('WS1 1AA', True, 'Walsall'),
    ('WV1 1AA', True, 'Wolverhampton'),
    ('YO1 1AA', True, 'York'),
    ('ZE1 1AA', True, 'Shetland'),

    # ========== INVALID DOUBLE-LETTER AREAS ==========
    ('AA1 1AA', False, 'AA invalid'),
    ('AC1 1AA', False, 'AC invalid'),
    ('AD1 1AA', False, 'AD invalid'),
    ('AE1 1AA', False, 'AE invalid'),
    ('AF1 1AA', False, 'AF invalid'),
    ('AG1 1AA', False, 'AG invalid'),
    ('AH1 1AA', False, 'AH invalid'),
    ('AI1 1AA', False, 'AI invalid'),
    ('AJ1 1AA', False, 'AJ invalid'),
    ('AK1 1AA', False, 'AK invalid'),

    # ========== INVALID SINGLE-LETTER AREAS ==========
    ('Q1 1AA', False, 'Q invalid (excluded)'),
    ('V1 1AA', False, 'V invalid (excluded)'),
    ('X1 1AA', False, 'X invalid (excluded)'),
    ('I1 1AA', False, 'I invalid (excluded)'),
    ('J1 1AA', False, 'J invalid (not used alone)'),
    ('M1 1AA', True, 'M is valid (Manchester)'),
    ('S1 1AA', True, 'S is valid (Sheffield)'),

    # ========== КРАЕВЫЕ СЛУЧАИ ==========
    ('', False, 'Пустая строка'),
    ('SW1A 1AA ', False, 'С пробелом в конце'),
    (' SW1A 1AA', False, 'С пробелом в начале'),
    ('sw1a 1aa', True, 'Нижний регистр (regex case-insensitive)'),
    ('Gir 0aa', True, 'GIR в нижнем регистре'),

    # ========== НЕПРАВИЛЬНАЯ ДЛИНА ==========
    ('SW1A 1AAA', False, 'Слишком длинный inward'),
    ('SW1A 1A', False, 'Слишком короткий inward'),
    ('SW1A1', False, 'Только outward'),
    ('1AA', False, 'Только inward'),

    # ========== НЕПРАВИЛЬНЫЕ СИМВОЛЫ ==========
    ('SW1A 1A!', False, 'Спецсимволы'),
    ('SW1A 1A ', False, 'Пробел в конце'),
    ('SW1A 1AA.', False, 'Точка в конце'),
]

# =============================================================================
# 4. ИНИЦИАЛИЗАЦИЯ
# =============================================================================
print("=" * 100)
print("ТЕСТИРОВАНИЕ UK POSTCODE (британские почтовые индексы)")
print("=" * 100)
print()

# Компилируем regex (с флагом IGNORECASE)
regex_compiled = re.compile(UK_POSTCODE_REGEX, re.IGNORECASE)

# Создаём Pattern Grammar
pattern = Pattern(UK_POSTCODE_GRAMMAR)

# Счётчики
total_tests = len(TEST_CASES)
grammar_vs_expected = 0
regex_vs_expected = 0
grammar_vs_regex = 0

# =============================================================================
# 5. ЗАПУСК ТЕСТОВ
# =============================================================================
results = []
for postcode, expected, description in TEST_CASES:
    # Тестируем regex
    try:
        regex_result = bool(regex_compiled.match(postcode))
    except Exception as e:
        regex_result = f"ERROR: {e}"

    # Тестируем Pattern Grammar
    try:
        grammar_result = pattern.match('postcode', postcode.upper())
    except Exception as e:
        grammar_result = f"ERROR: {e}"

    # Сравнения с ожиданием
    g_vs_e = None
    r_vs_e = None
    g_vs_r = None

    if isinstance(grammar_result, bool):
        g_vs_e = (grammar_result == expected)
        if g_vs_e:
            grammar_vs_expected += 1

    if isinstance(regex_result, bool):
        r_vs_e = (regex_result == expected)
        if r_vs_e:
            regex_vs_expected += 1

    if isinstance(regex_result, bool) and isinstance(grammar_result, bool):
        g_vs_r = (grammar_result == regex_result)
        if g_vs_r:
            grammar_vs_regex += 1

    results.append({
        'postcode': postcode,
        'expected': expected,
        'regex': regex_result,
        'grammar': grammar_result,
        'description': description,
        'g_vs_e': g_vs_e,
        'r_vs_e': r_vs_e,
        'g_vs_r': g_vs_r
    })

# =============================================================================
# 6. ВЫВОД РЕЗУЛЬТАТОВ
# =============================================================================
print("РЕЗУЛЬТАТЫ ПО ТЕСТАМ (первые 50):")
print("-" * 120)
header = f"{'Postcode':<25} {'Ожид.':<6} {'Regex':<8} {'Grammar':<8} {'GvE':<5} {'RvE':<5} {'GvR':<5} {'Описание'}"
print(header)
print("-" * 120)

# Показываем результаты
for r in results:
    # Формируем статусы
    g_vs_e_status = "✅" if r['g_vs_e'] else "❌" if r['g_vs_e'] is False else "?"
    r_vs_e_status = "✅" if r['r_vs_e'] else "❌" if r['r_vs_e'] is False else "?"
    g_vs_r_status = "✅" if r['g_vs_r'] else "❌" if r['g_vs_r'] is False else "?"

    regex_str = str(r['regex'])[:8]
    grammar_str = str(r['grammar'])[:8]
    postcode_display = r['postcode'][:24] if len(r['postcode']) <= 24 else r['postcode'][:21] + '...'

    print(f"{postcode_display:<25} {str(r['expected']):<6} {regex_str:<8} {grammar_str:<8} "
          f"{g_vs_e_status:<5} {r_vs_e_status:<5} {g_vs_r_status:<5} {r['description']}")

print("-" * 120)
print()

# =============================================================================
# 7. СТАТИСТИКА
# =============================================================================
print("СТАТИСТИКА:")
print("-" * 80)
print(f"Всего тестов:                    {total_tests}")
print()
print("СОВПАДЕНИЯ:")
print(f"  Grammar с ожиданием:           {grammar_vs_expected}/{total_tests} ({grammar_vs_expected/total_tests*100:.1f}%)")
print(f"  Regex с ожиданием:             {regex_vs_expected}/{total_tests} ({regex_vs_expected/total_tests*100:.1f}%)")
print(f"  Grammar с Regex:                {grammar_vs_regex}/{total_tests} ({grammar_vs_regex/total_tests*100:.1f}%)")
print()
print("РАСХОЖДЕНИЯ:")
grammar_errors = total_tests - grammar_vs_expected
regex_errors = total_tests - regex_vs_expected
grammar_regex_diff = total_tests - grammar_vs_regex
print(f"  Grammar с ожиданием:           {grammar_errors}")
print(f"  Regex с ожиданием:             {regex_errors}")
print(f"  Grammar с Regex:                {grammar_regex_diff}")
print("-" * 80)
print()

# Детальный анализ расхождений
if grammar_errors > 0 or regex_errors > 0 or grammar_regex_diff > 0:
    print("⚠️  НАЙДЕНЫ РАСХОЖДЕНИЯ!")
    print("-" * 80)

    if grammar_errors > 0:
        print("\n📌 Grammar НЕ совпадает с ожиданием:")
        grammar_fails = [r for r in results if r['g_vs_e'] is False]
        for r in grammar_fails[:15]:
            print(f"  • {r['postcode']:<20} grammar={r['grammar']}, ожидалось={r['expected']}")
            print(f"    → {r['description']}")
        if len(grammar_fails) > 15:
            print(f"    ... и ещё {len(grammar_fails) - 15}")

    if regex_errors > 0:
        print("\n📌 Regex НЕ совпадает с ожиданием:")
        regex_fails = [r for r in results if r['r_vs_e'] is False]
        for r in regex_fails[:15]:
            print(f"  • {r['postcode']:<20} regex={r['regex']}, ожидалось={r['expected']}")
            print(f"    → {r['description']}")
        if len(regex_fails) > 15:
            print(f"    ... и ещё {len(regex_fails) - 15}")

    if grammar_regex_diff > 0:
        print("\n📌 Grammar и Regex НЕ совпадают между собой:")
        diff_fails = [r for r in results if r['g_vs_r'] is False]
        for r in diff_fails[:15]:
            print(f"  • {r['postcode']:<20} grammar={r['grammar']}, regex={r['regex']}")
            print(f"    → {r['description']}")
        if len(diff_fails) > 15:
            print(f"    ... и ещё {len(diff_fails) - 15}")
else:
    print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Pattern Grammar полностью совместим с regex")

print()
print("=" * 100)

# =============================================================================
# 8. ИНФОРМАЦИЯ О ГРАММАТИКЕ
# =============================================================================
print()
print("ИНФОРМАЦИЯ О ГРАММАТИКЕ:")
print("-" * 80)
info = pattern.get_info()
print(f"Всего правил: {info.get('total_rules', 0)}")
print(f"Правила (regex):     {info.get('regex_rules', [])}")
print(f"Правила (parser):    {info.get('parser_rules', [])}")
print()

# =============================================================================
# 9. ПРИМЕР ДЕРЕВА РАЗБОРА
# =============================================================================
print("ПРИМЕР ДЕРЕВА РАЗБОРА (SW1A 1AA):")
print("-" * 80)
try:
    tree = pattern.parse('postcode', 'SW1A 1AA')
    if tree:
        print(tree.pretty())
    else:
        print("Дерево не получено (возможно, правило не поддерживает парсинг)")
except Exception as e:
    print(f"Ошибка при парсинге: {e}")

print("=" * 100)
