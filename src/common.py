import enum

from google.auth.transport import requests
from google.oauth2 import id_token
from pydantic import BaseModel

from src.config import Config


class CommonHeaders(BaseModel):
    authorization: str


def strtobool(val):
    """Convert a string representation of truth to true (1) or false (0).
    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
    are 'n', 'no', 'f', 'false', 'off', and '0'.  Raises ValueError if
    'val' is anything else.
    """
    val = val.lower()
    if val in ("y", "yes", "t", "true", "on", "1"):
        return True
    elif val in ("n", "no", "f", "false", "off", "0"):
        return False
    else:
        raise ValueError("invalid truth value %r" % (val,))


def decode_token(token: str):
    return id_token.verify_oauth2_token(
        token, requests.Request(), Config.GOOGLE_CLIENT_ID
    )


class IsoCountryCode(str, enum.Enum):
    ABW = "ABW"  # Aruba
    AFG = "AFG"  # Afghanistan
    AGO = "AGO"  # Angola
    AIA = "AIA"  # Anguilla
    ALA = "ALA"  # Åland Islands
    ALB = "ALB"  # Albania
    AND = "AND"  # Andorra
    ARE = "ARE"  # United Arab Emirates
    ARG = "ARG"  # Argentina
    ARM = "ARM"  # Armenia
    ASM = "ASM"  # American Samoa
    ATA = "ATA"  # Antarctica
    ATF = "ATF"  # French Southern Territories
    ATG = "ATG"  # Antigua and Barbuda
    AUS = "AUS"  # Australia
    AUT = "AUT"  # Austria
    AZE = "AZE"  # Azerbaijan
    BDI = "BDI"  # Burundi
    BEL = "BEL"  # Belgium
    BEN = "BEN"  # Benin
    BES = "BES"  # Bonaire, Sint Eustatius and Saba
    BFA = "BFA"  # Burkina Faso
    BGD = "BGD"  # Bangladesh
    BGR = "BGR"  # Bulgaria
    BHR = "BHR"  # Bahrain
    BHS = "BHS"  # Bahamas
    BIH = "BIH"  # Bosnia and Herzegovina
    BLM = "BLM"  # Saint Barthélemy
    BLR = "BLR"  # Belarus
    BLZ = "BLZ"  # Belize
    BMU = "BMU"  # Bermuda
    BOL = "BOL"  # Bolivia, Plurinational State of
    BRA = "BRA"  # Brazil
    BRB = "BRB"  # Barbados
    BRN = "BRN"  # Brunei Darussalam
    BTN = "BTN"  # Bhutan
    BVT = "BVT"  # Bouvet Island
    BWA = "BWA"  # Botswana
    CAF = "CAF"  # Central African Republic
    CAN = "CAN"  # Canada
    CCK = "CCK"  # Cocos (Keeling) Islands
    CHE = "CHE"  # Switzerland
    CHL = "CHL"  # Chile
    CHN = "CHN"  # China
    CIV = "CIV"  # Côte d'Ivoire
    CMR = "CMR"  # Cameroon
    COD = "COD"  # Congo, Democratic Republic of the
    COG = "COG"  # Congo
    COK = "COK"  # Cook Islands
    COL = "COL"  # Colombia
    COM = "COM"  # Comoros
    CPV = "CPV"  # Cabo Verde
    CRI = "CRI"  # Costa Rica
    CUB = "CUB"  # Cuba
    CUW = "CUW"  # Curaçao
    CXR = "CXR"  # Christmas Island
    CYM = "CYM"  # Cayman Islands
    CYP = "CYP"  # Cyprus
    CZE = "CZE"  # Czechia
    DEU = "DEU"  # Germany
    DJI = "DJI"  # Djibouti
    DMA = "DMA"  # Dominica
    DNK = "DNK"  # Denmark
    DOM = "DOM"  # Dominican Republic
    DZA = "DZA"  # Algeria
    ECU = "ECU"  # Ecuador
    EGY = "EGY"  # Egypt
    ERI = "ERI"  # Eritrea
    ESH = "ESH"  # Western Sahara
    ESP = "ESP"  # Spain
    EST = "EST"  # Estonia
    ETH = "ETH"  # Ethiopia
    FIN = "FIN"  # Finland
    FJI = "FJI"  # Fiji
    FLK = "FLK"  # Falkland Islands (Malvinas)
    FRA = "FRA"  # France
    FRO = "FRO"  # Faroe Islands
    FSM = "FSM"  # Micronesia, Federated States of
    GAB = "GAB"  # Gabon
    GBR = "GBR"  # United Kingdom of Great Britain and Northern Ireland
    GEO = "GEO"  # Georgia
    GGY = "GGY"  # Guernsey
    GHA = "GHA"  # Ghana
    GIB = "GIB"  # Gibraltar
    GIN = "GIN"  # Guinea
    GLP = "GLP"  # Guadeloupe
    GMB = "GMB"  # Gambia
    GNB = "GNB"  # Guinea-Bissau
    GNQ = "GNQ"  # Equatorial Guinea
    GRC = "GRC"  # Greece
    GRD = "GRD"  # Grenada
    GRL = "GRL"  # Greenland
    GTM = "GTM"  # Guatemala
    GUF = "GUF"  # French Guiana
    GUM = "GUM"  # Guam
    GUY = "GUY"  # Guyana
    HKG = "HKG"  # Hong Kong
    HMD = "HMD"  # Heard Island and McDonald Islands
    HND = "HND"  # Honduras
    HRV = "HRV"  # Croatia
    HTI = "HTI"  # Haiti
    HUN = "HUN"  # Hungary
    IDN = "IDN"  # Indonesia
    IMN = "IMN"  # Isle of Man
    IND = "IND"  # India
    IOT = "IOT"  # British Indian Ocean Territory
    IRL = "IRL"  # Ireland
    IRN = "IRN"  # Iran, Islamic Republic of
    IRQ = "IRQ"  # Iraq
    ISL = "ISL"  # Iceland
    ISR = "ISR"  # Israel
    ITA = "ITA"  # Italy
    JAM = "JAM"  # Jamaica
    JEY = "JEY"  # Jersey
    JOR = "JOR"  # Jordan
    JPN = "JPN"  # Japan
    KAZ = "KAZ"  # Kazakhstan
    KEN = "KEN"  # Kenya
    KGZ = "KGZ"  # Kyrgyzstan
    KHM = "KHM"  # Cambodia
    KIR = "KIR"  # Kiribati
    KNA = "KNA"  # Saint Kitts and Nevis
    KOR = "KOR"  # Korea, Republic of
    KWT = "KWT"  # Kuwait
    LAO = "LAO"  # Lao People's Democratic Republic
    LBN = "LBN"  # Lebanon
    LBR = "LBR"  # Liberia
    LBY = "LBY"  # Libya
    LCA = "LCA"  # Saint Lucia
    LIE = "LIE"  # Liechtenstein
    LKA = "LKA"  # Sri Lanka
    LSO = "LSO"  # Lesotho
    LTU = "LTU"  # Lithuania
    LUX = "LUX"  # Luxembourg
    LVA = "LVA"  # Latvia
    MAC = "MAC"  # Macao
    MAF = "MAF"  # Saint Martin (French part)
    MAR = "MAR"  # Morocco
    MCO = "MCO"  # Monaco
    MDA = "MDA"  # Moldova, Republic of
    MDG = "MDG"  # Madagascar
    MDV = "MDV"  # Maldives
    MEX = "MEX"  # Mexico
    MHL = "MHL"  # Marshall Islands
    MKD = "MKD"  # North Macedonia
    MLI = "MLI"  # Mali
    MLT = "MLT"  # Malta
    MMR = "MMR"  # Myanmar
    MNE = "MNE"  # Montenegro
    MNG = "MNG"  # Mongolia
    MNP = "MNP"  # Northern Mariana Islands
    MOZ = "MOZ"  # Mozambique
    MRT = "MRT"  # Mauritania
    MSR = "MSR"  # Montserrat
    MTQ = "MTQ"  # Martinique
    MUS = "MUS"  # Mauritius
    MWI = "MWI"  # Malawi
    MYS = "MYS"  # Malaysia
    MYT = "MYT"  # Mayotte
    NAM = "NAM"  # Namibia
    NCL = "NCL"  # New Caledonia
    NER = "NER"  # Niger
    NFK = "NFK"  # Norfolk Island
    NGA = "NGA"  # Nigeria
    NIC = "NIC"  # Nicaragua
    NIU = "NIU"  # Niue
    NLD = "NLD"  # Netherlands, Kingdom of the
    NOR = "NOR"  # Norway
    NPL = "NPL"  # Nepal
    NRU = "NRU"  # Nauru
    NZL = "NZL"  # New Zealand
    OMN = "OMN"  # Oman
    PAK = "PAK"  # Pakistan
    PAN = "PAN"  # Panama
    PCN = "PCN"  # Pitcairn
    PER = "PER"  # Peru
    PHL = "PHL"  # Philippines
    PLW = "PLW"  # Palau
    PNG = "PNG"  # Papua New Guinea
    POL = "POL"  # Poland
    PRI = "PRI"  # Puerto Rico
    PRK = "PRK"  # Korea, Democratic People's Republic of
    PRT = "PRT"  # Portugal
    PRY = "PRY"  # Paraguay
    PSE = "PSE"  # Palestine, State of
    PYF = "PYF"  # French Polynesia
    QAT = "QAT"  # Qatar
    REU = "REU"  # Réunion
    ROU = "ROU"  # Romania
    RUS = "RUS"  # Russian Federation
    RWA = "RWA"  # Rwanda
    SAU = "SAU"  # Saudi Arabia
    SDN = "SDN"  # Sudan
    SEN = "SEN"  # Senegal
    SGP = "SGP"  # Singapore
    SGS = "SGS"  # South Georgia and the South Sandwich Islands
    SHN = "SHN"  # Saint Helena, Ascension and Tristan da Cunha
    SJM = "SJM"  # Svalbard and Jan Mayen
    SLB = "SLB"  # Solomon Islands
    SLE = "SLE"  # Sierra Leone
    SLV = "SLV"  # El Salvador
    SMR = "SMR"  # San Marino
    SOM = "SOM"  # Somalia
    SPM = "SPM"  # Saint Pierre and Miquelon
    SRB = "SRB"  # Serbia
    SSD = "SSD"  # South Sudan
    STP = "STP"  # Sao Tome and Principe
    SUR = "SUR"  # Suriname
    SVK = "SVK"  # Slovakia
    SVN = "SVN"  # Slovenia
    SWE = "SWE"  # Sweden
    SWZ = "SWZ"  # Eswatini
    SXM = "SXM"  # Sint Maarten (Dutch part)
    SYC = "SYC"  # Seychelles
    SYR = "SYR"  # Syrian Arab Republic
    TCA = "TCA"  # Turks and Caicos Islands
    TCD = "TCD"  # Chad
    TGO = "TGO"  # Togo
    THA = "THA"  # Thailand
    TJK = "TJK"  # Tajikistan
    TKL = "TKL"  # Tokelau
    TKM = "TKM"  # Turkmenistan
    TLS = "TLS"  # Timor-Leste
    TON = "TON"  # Tonga
    TTO = "TTO"  # Trinidad and Tobago
    TUN = "TUN"  # Tunisia
    TUR = "TUR"  # Türkiye
    TUV = "TUV"  # Tuvalu
    TWN = "TWN"  # Taiwan, Province of China
    TZA = "TZA"  # Tanzania, United Republic of
    UGA = "UGA"  # Uganda
    UKR = "UKR"  # Ukraine
    UMI = "UMI"  # United States Minor Outlying Islands
    URY = "URY"  # Uruguay
    USA = "USA"  # United States of America
    UZB = "UZB"  # Uzbekistan
    VAT = "VAT"  # Holy See
    VCT = "VCT"  # Saint Vincent and the Grenadines
    VEN = "VEN"  # Venezuela, Bolivarian Republic of
    VGB = "VGB"  # Virgin Islands (British)
    VIR = "VIR"  # Virgin Islands (U.S.)
    VNM = "VNM"  # Viet Nam
    VUT = "VUT"  # Vanuatu
    WLF = "WLF"  # Wallis and Futuna
    WSM = "WSM"  # Samoa
    YEM = "YEM"  # Yemen
    ZAF = "ZAF"  # South Africa
    ZMB = "ZMB"  # Zambia
    ZWE = "ZWE"  # Zimbabwe


class MuscleGroup(str, enum.Enum):
    CHEST = "chest"
    BACK = "back"
    LEGS = "legs"
    ARMS = "arms"
    SHOULDERS = "shoulders"
    CORE = "core"
    FULL_BODY = "full body"
    CARDIO = "cardio"
    OTHER = "other"


class SpecificMuscle(str, enum.Enum):
    BICEPS = "biceps"
    TRICEPS = "triceps"
    QUADRICEPS = "quadriceps"
    HAMSTRINGS = "hamstrings"
    GLUTES = "glutes"
    CALVES = "calves"
    DELTOIDS = "deltoids"
    PECTORALS = "pectorals"
    LATS = "lats"
    TRAPS = "traps"
    ABS = "abs"
    OBLIQUES = "obliques"
    FOREARMS = "forearms"
    RHOMBOIDS = "rhomboids"
    OTHER = "other"
