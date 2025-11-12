"""
Geographic Features for Location-Based Clustering - Phase 3

Enhances clustering by considering geographic proximity and location-based relationships.
Helps group stories that occur in the same geographic areas or regions.
"""
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from math import radians, sin, cos, sqrt, atan2
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class GeographicLocation:
    """Represents a geographic location with coordinates and metadata"""
    name: str
    latitude: float
    longitude: float
    location_type: str  # city, state, country, region, continent
    population: Optional[int] = None
    country_code: Optional[str] = None
    admin_level: Optional[int] = None  # For hierarchical relationships

    def distance_to(self, other: 'GeographicLocation') -> float:
        """
        Calculate distance to another location in kilometers (Haversine formula)

        Args:
            other: Another GeographicLocation

        Returns:
            Distance in kilometers
        """
        R = 6371  # Earth's radius in kilometers

        lat1_rad, lon1_rad = radians(self.latitude), radians(self.longitude)
        lat2_rad, lon2_rad = radians(other.latitude), radians(other.longitude)

        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = sin(dlat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))

        return R * c


class GeographicFeatureExtractor:
    """
    Extracts and analyzes geographic features from news articles.

    Provides location-based similarity scoring for clustering.
    """

    def __init__(self):
        """Initialize with geographic knowledge base"""
        # Major world cities with coordinates
        self.major_cities = {
            'New York': GeographicLocation('New York', 40.7128, -74.0060, 'city', 8419000, 'US'),
            'London': GeographicLocation('London', 51.5074, -0.1278, 'city', 8982000, 'GB'),
            'Tokyo': GeographicLocation('Tokyo', 35.6762, 139.6503, 'city', 13960000, 'JP'),
            'Paris': GeographicLocation('Paris', 48.8566, 2.3522, 'city', 2161000, 'FR'),
            'Beijing': GeographicLocation('Beijing', 39.9042, 116.4074, 'city', 21540000, 'CN'),
            'Los Angeles': GeographicLocation('Los Angeles', 34.0522, -118.2437, 'city', 3990000, 'US'),
            'Chicago': GeographicLocation('Chicago', 41.8781, -87.6298, 'city', 2716000, 'US'),
            'Houston': GeographicLocation('Houston', 29.7604, -95.3698, 'city', 2328000, 'US'),
            'Phoenix': GeographicLocation('Phoenix', 33.4484, -112.0740, 'city', 1660000, 'US'),
            'Philadelphia': GeographicLocation('Philadelphia', 39.9526, -75.1652, 'city', 1584000, 'US'),
            'San Antonio': GeographicLocation('San Antonio', 29.4241, -98.4936, 'city', 1547000, 'US'),
            'San Diego': GeographicLocation('San Diego', 32.7157, -117.1611, 'city', 1424000, 'US'),
            'Dallas': GeographicLocation('Dallas', 32.7767, -96.7970, 'city', 1341000, 'US'),
            'San Jose': GeographicLocation('San Jose', 37.3382, -121.8863, 'city', 1035000, 'US'),
            'Austin': GeographicLocation('Austin', 30.2672, -97.7431, 'city', 964000, 'US'),
            'Jacksonville': GeographicLocation('Jacksonville', 30.3322, -81.6557, 'city', 949000, 'US'),
            'Fort Worth': GeographicLocation('Fort Worth', 32.7555, -97.3308, 'city', 935000, 'US'),
            'Columbus': GeographicLocation('Columbus', 39.9612, -82.9988, 'city', 905000, 'US'),
            'Charlotte': GeographicLocation('Charlotte', 35.2271, -80.8431, 'city', 900000, 'US'),
            'San Francisco': GeographicLocation('San Francisco', 37.7749, -122.4194, 'city', 875000, 'US'),
            'Seattle': GeographicLocation('Seattle', 47.6062, -122.3321, 'city', 738000, 'US'),
            'Denver': GeographicLocation('Denver', 39.7392, -104.9903, 'city', 715000, 'US'),
            'Boston': GeographicLocation('Boston', 42.3601, -71.0589, 'city', 675000, 'US'),
            'El Paso': GeographicLocation('El Paso', 31.7619, -106.4850, 'city', 681000, 'US'),
            'Detroit': GeographicLocation('Detroit', 42.3314, -83.0458, 'city', 675000, 'US'),
            'Washington': GeographicLocation('Washington', 38.9072, -77.0369, 'city', 689500, 'US'),
            'Memphis': GeographicLocation('Memphis', 35.1495, -90.0490, 'city', 652000, 'US'),
            'Nashville': GeographicLocation('Nashville', 36.1627, -86.7816, 'city', 694000, 'US'),
            'Portland': GeographicLocation('Portland', 45.5152, -122.6784, 'city', 653000, 'US'),
            'Oklahoma City': GeographicLocation('Oklahoma City', 35.4676, -97.5164, 'city', 649000, 'US'),
            'Las Vegas': GeographicLocation('Las Vegas', 36.1699, -115.1398, 'city', 641000, 'US'),
            'Baltimore': GeographicLocation('Baltimore', 39.2904, -76.6122, 'city', 593000, 'US'),
            'Louisville': GeographicLocation('Louisville', 38.2527, -85.7585, 'city', 617000, 'US'),
            'Milwaukee': GeographicLocation('Milwaukee', 43.0389, -87.9065, 'city', 577000, 'US'),
            'Albuquerque': GeographicLocation('Albuquerque', 35.0844, -106.6504, 'city', 565000, 'US'),
            'Tucson': GeographicLocation('Tucson', 32.2226, -110.9747, 'city', 550000, 'US'),
            'Fresno': GeographicLocation('Fresno', 36.7378, -119.7871, 'city', 530000, 'US'),
            'Sacramento': GeographicLocation('Sacramento', 38.5816, -121.4944, 'city', 525000, 'US'),
            'Mesa': GeographicLocation('Mesa', 33.4152, -111.8315, 'city', 518000, 'US'),
            'Kansas City': GeographicLocation('Kansas City', 39.0997, -94.5786, 'city', 508000, 'US'),
            'Atlanta': GeographicLocation('Atlanta', 33.7490, -84.3880, 'city', 498000, 'US'),
            'Long Beach': GeographicLocation('Long Beach', 33.7701, -118.1937, 'city', 466000, 'US'),
            'Colorado Springs': GeographicLocation('Colorado Springs', 38.8339, -104.8214, 'city', 480000, 'US'),
            'Raleigh': GeographicLocation('Raleigh', 35.7796, -78.6382, 'city', 470000, 'US'),
            'Miami': GeographicLocation('Miami', 25.7617, -80.1918, 'city', 470000, 'US'),
            'Virginia Beach': GeographicLocation('Virginia Beach', 36.8529, -75.9780, 'city', 450000, 'US'),
            'Omaha': GeographicLocation('Omaha', 41.2565, -95.9345, 'city', 480000, 'US'),
            'Oakland': GeographicLocation('Oakland', 37.8044, -122.2711, 'city', 440000, 'US'),
            'Minneapolis': GeographicLocation('Minneapolis', 44.9778, -93.2650, 'city', 430000, 'US'),
            'Tulsa': GeographicLocation('Tulsa', 36.1540, -95.9928, 'city', 400000, 'US'),
            'Wichita': GeographicLocation('Wichita', 37.6872, -97.3301, 'city', 390000, 'US'),
            'New Orleans': GeographicLocation('New Orleans', 29.9511, -90.0715, 'city', 390000, 'US'),
            'Cleveland': GeographicLocation('Cleveland', 41.4993, -81.6944, 'city', 380000, 'US'),
            'Tampa': GeographicLocation('Tampa', 27.9506, -82.4572, 'city', 400000, 'US'),
            'Bakersfield': GeographicLocation('Bakersfield', 35.3733, -119.0187, 'city', 400000, 'US'),
            'Aurora': GeographicLocation('Aurora', 39.7294, -104.8319, 'city', 380000, 'US'),
            'Anaheim': GeographicLocation('Anaheim', 33.8366, -117.9143, 'city', 350000, 'US'),
            'Honolulu': GeographicLocation('Honolulu', 21.3069, -157.8583, 'city', 350000, 'US'),
            'Santa Ana': GeographicLocation('Santa Ana', 33.7455, -117.8677, 'city', 330000, 'US'),
            'Corpus Christi': GeographicLocation('Corpus Christi', 27.8006, -97.3964, 'city', 325000, 'US'),
            'Riverside': GeographicLocation('Riverside', 33.9806, -117.3755, 'city', 330000, 'US'),
            'Lexington': GeographicLocation('Lexington', 38.0406, -84.5037, 'city', 320000, 'US'),
            'Stockton': GeographicLocation('Stockton', 37.9577, -121.2908, 'city', 320000, 'US'),
            'Henderson': GeographicLocation('Henderson', 36.0395, -114.9817, 'city', 320000, 'US'),
            'Saint Paul': GeographicLocation('Saint Paul', 44.9537, -93.0900, 'city', 310000, 'US'),
            'St. Louis': GeographicLocation('St. Louis', 38.6270, -90.1994, 'city', 300000, 'US'),
            'Cincinnati': GeographicLocation('Cincinnati', 39.1031, -84.5120, 'city', 300000, 'US'),
            'Pittsburgh': GeographicLocation('Pittsburgh', 40.4406, -79.9959, 'city', 300000, 'US'),
            'Greensboro': GeographicLocation('Greensboro', 36.0726, -79.7920, 'city', 300000, 'US'),
            'Anchorage': GeographicLocation('Anchorage', 61.2181, -149.9003, 'city', 290000, 'US'),
            'Plano': GeographicLocation('Plano', 33.0198, -96.6989, 'city', 290000, 'US'),
            'Lincoln': GeographicLocation('Lincoln', 40.8136, -96.7026, 'city', 290000, 'US'),
            'Orlando': GeographicLocation('Orlando', 28.5383, -81.3792, 'city', 290000, 'US'),
            'Irvine': GeographicLocation('Irvine', 33.6846, -117.8265, 'city', 290000, 'US'),
            'Newark': GeographicLocation('Newark', 40.7357, -74.1724, 'city', 280000, 'US'),
            'Durham': GeographicLocation('Durham', 35.9940, -78.8986, 'city', 280000, 'US'),
            'Chula Vista': GeographicLocation('Chula Vista', 32.6401, -117.0842, 'city', 280000, 'US'),
            'Toledo': GeographicLocation('Toledo', 41.6528, -83.5379, 'city', 270000, 'US'),
            'Fort Wayne': GeographicLocation('Fort Wayne', 41.0793, -85.1394, 'city', 270000, 'US'),
            'St. Petersburg': GeographicLocation('St. Petersburg', 27.7663, -82.6404, 'city', 270000, 'US'),
            'Laredo': GeographicLocation('Laredo', 27.5064, -99.5075, 'city', 270000, 'US'),
            'Jersey City': GeographicLocation('Jersey City', 40.7178, -74.0431, 'city', 270000, 'US'),
            'Chandler': GeographicLocation('Chandler', 33.3062, -111.8413, 'city', 270000, 'US'),
            'Madison': GeographicLocation('Madison', 43.0731, -89.4012, 'city', 270000, 'US'),
            'Lubbock': GeographicLocation('Lubbock', 33.5779, -101.8552, 'city', 260000, 'US'),
            'Scottsdale': GeographicLocation('Scottsdale', 33.4942, -111.9261, 'city', 260000, 'US'),
            'Reno': GeographicLocation('Reno', 39.5296, -119.8138, 'city', 260000, 'US'),
            'Buffalo': GeographicLocation('Buffalo', 42.8864, -78.8784, 'city', 260000, 'US'),
            'Gilbert': GeographicLocation('Gilbert', 33.3528, -111.7890, 'city', 260000, 'US'),
            'Glendale': GeographicLocation('Glendale', 33.5387, -112.1859, 'city', 250000, 'US'),
            'Winston-Salem': GeographicLocation('Winston-Salem', 36.0999, -80.2442, 'city', 250000, 'US'),
            'Chesapeake': GeographicLocation('Chesapeake', 36.7682, -76.2875, 'city', 250000, 'US'),
            'Norfolk': GeographicLocation('Norfolk', 36.8508, -76.2859, 'city', 250000, 'US'),
            'Fremont': GeographicLocation('Fremont', 37.5485, -121.9886, 'city', 250000, 'US'),
            'Garland': GeographicLocation('Garland', 32.9126, -96.6389, 'city', 250000, 'US'),
            'Irving': GeographicLocation('Irving', 32.8140, -96.9489, 'city', 250000, 'US'),
            'Hialeah': GeographicLocation('Hialeah', 25.8576, -80.2781, 'city', 250000, 'US'),
            'Richmond': GeographicLocation('Richmond', 37.5407, -77.4360, 'city', 250000, 'US'),
            'Boise': GeographicLocation('Boise', 43.6150, -114.2116, 'city', 235000, 'US'),
            'Spokane': GeographicLocation('Spokane', 47.6587, -117.4260, 'city', 230000, 'US'),
            'Baton Rouge': GeographicLocation('Baton Rouge', 30.4515, -91.1871, 'city', 225000, 'US'),
        }

        # US States
        self.us_states = {
            'Alabama': GeographicLocation('Alabama', 32.806671, -86.791130, 'state', 5024279, 'US'),
            'Alaska': GeographicLocation('Alaska', 61.370716, -152.404419, 'state', 732923, 'US'),
            'Arizona': GeographicLocation('Arizona', 33.729759, -111.431221, 'state', 7359197, 'US'),
            'Arkansas': GeographicLocation('Arkansas', 34.969704, -92.373123, 'state', 3011524, 'US'),
            'California': GeographicLocation('California', 36.116203, -119.681564, 'state', 39237836, 'US'),
            'Colorado': GeographicLocation('Colorado', 39.059811, -105.311104, 'state', 5773714, 'US'),
            'Connecticut': GeographicLocation('Connecticut', 41.597782, -72.755371, 'state', 3605944, 'US'),
            'Delaware': GeographicLocation('Delaware', 39.318523, -75.507141, 'state', 989948, 'US'),
            'Florida': GeographicLocation('Florida', 27.766279, -81.686783, 'state', 22244823, 'US'),
            'Georgia': GeographicLocation('Georgia', 33.040619, -83.643074, 'state', 10711908, 'US'),
            'Hawaii': GeographicLocation('Hawaii', 21.094318, -157.498337, 'state', 1440196, 'US'),
            'Idaho': GeographicLocation('Idaho', 44.240459, -114.478828, 'state', 1939033, 'US'),
            'Illinois': GeographicLocation('Illinois', 40.349457, -88.986137, 'state', 12582032, 'US'),
            'Indiana': GeographicLocation('Indiana', 39.849426, -86.258278, 'state', 6785528, 'US'),
            'Iowa': GeographicLocation('Iowa', 42.011539, -93.210526, 'state', 3190369, 'US'),
            'Kansas': GeographicLocation('Kansas', 38.526600, -96.726486, 'state', 2937880, 'US'),
            'Kentucky': GeographicLocation('Kentucky', 37.668140, -84.670067, 'state', 4505836, 'US'),
            'Louisiana': GeographicLocation('Louisiana', 31.169546, -91.867805, 'state', 4657757, 'US'),
            'Maine': GeographicLocation('Maine', 44.693947, -69.381927, 'state', 1362359, 'US'),
            'Maryland': GeographicLocation('Maryland', 39.063946, -76.802101, 'state', 6177224, 'US'),
            'Massachusetts': GeographicLocation('Massachusetts', 42.230171, -71.530106, 'state', 7001399, 'US'),
            'Michigan': GeographicLocation('Michigan', 43.326618, -84.536095, 'state', 10034113, 'US'),
            'Minnesota': GeographicLocation('Minnesota', 45.694454, -93.900192, 'state', 5737915, 'US'),
            'Mississippi': GeographicLocation('Mississippi', 32.741646, -89.678696, 'state', 2961279, 'US'),
            'Missouri': GeographicLocation('Missouri', 38.456085, -92.288368, 'state', 6196540, 'US'),
            'Montana': GeographicLocation('Montana', 46.921925, -110.454353, 'state', 1084225, 'US'),
            'Nebraska': GeographicLocation('Nebraska', 41.125370, -98.268082, 'state', 1961504, 'US'),
            'Nevada': GeographicLocation('Nevada', 38.313515, -117.055374, 'state', 3177772, 'US'),
            'New Hampshire': GeographicLocation('New Hampshire', 43.452492, -71.563896, 'state', 1377529, 'US'),
            'New Jersey': GeographicLocation('New Jersey', 40.298904, -74.521011, 'state', 9288994, 'US'),
            'New Mexico': GeographicLocation('New Mexico', 34.840515, -106.248482, 'state', 2117522, 'US'),
            'New York': GeographicLocation('New York', 42.165726, -74.948051, 'state', 19336776, 'US'),
            'North Carolina': GeographicLocation('North Carolina', 35.630066, -79.806419, 'state', 10611862, 'US'),
            'North Dakota': GeographicLocation('North Dakota', 47.528912, -99.784012, 'state', 779094, 'US'),
            'Ohio': GeographicLocation('Ohio', 40.388783, -82.764915, 'state', 11756058, 'US'),
            'Oklahoma': GeographicLocation('Oklahoma', 35.565342, -96.928917, 'state', 3959353, 'US'),
            'Oregon': GeographicLocation('Oregon', 44.572021, -122.070938, 'state', 4240137, 'US'),
            'Pennsylvania': GeographicLocation('Pennsylvania', 40.590752, -77.209755, 'state', 12972008, 'US'),
            'Rhode Island': GeographicLocation('Rhode Island', 41.680893, -71.511780, 'state', 1097379, 'US'),
            'South Carolina': GeographicLocation('South Carolina', 33.856892, -80.945007, 'state', 5282634, 'US'),
            'South Dakota': GeographicLocation('South Dakota', 44.299782, -99.438828, 'state', 909824, 'US'),
            'Tennessee': GeographicLocation('Tennessee', 35.747845, -86.692345, 'state', 7051339, 'US'),
            'Texas': GeographicLocation('Texas', 31.054487, -97.563461, 'state', 30097526, 'US'),
            'Utah': GeographicLocation('Utah', 40.150032, -111.862434, 'state', 3271616, 'US'),
            'Vermont': GeographicLocation('Vermont', 44.045876, -72.710686, 'state', 643077, 'US'),
            'Virginia': GeographicLocation('Virginia', 37.769337, -78.169968, 'state', 8683619, 'US'),
            'Washington': GeographicLocation('Washington', 47.400902, -121.490494, 'state', 7693612, 'US'),
            'West Virginia': GeographicLocation('West Virginia', 38.491226, -80.954071, 'state', 1793716, 'US'),
            'Wisconsin': GeographicLocation('Wisconsin', 44.268543, -89.616508, 'state', 5893718, 'US'),
            'Wyoming': GeographicLocation('Wyoming', 42.755966, -107.302490, 'state', 576851, 'US'),
        }

        # Countries
        self.countries = {
            'United States': GeographicLocation('United States', 37.0902, -95.7129, 'country', 331900000, 'US'),
            'China': GeographicLocation('China', 35.8617, 104.1954, 'country', 1441000000, 'CN'),
            'India': GeographicLocation('India', 20.5937, 78.9629, 'country', 1380000000, 'IN'),
            'Russia': GeographicLocation('Russia', 61.5240, 105.3188, 'country', 145900000, 'RU'),
            'Japan': GeographicLocation('Japan', 36.2048, 138.2529, 'country', 126500000, 'JP'),
            'Germany': GeographicLocation('Germany', 51.1657, 10.4515, 'country', 83200000, 'DE'),
            'France': GeographicLocation('France', 46.2276, 2.2137, 'country', 67800000, 'FR'),
            'United Kingdom': GeographicLocation('United Kingdom', 55.3781, -3.4360, 'country', 67500000, 'GB'),
            'Italy': GeographicLocation('Italy', 41.8719, 12.5674, 'country', 60400000, 'IT'),
            'Brazil': GeographicLocation('Brazil', -14.2350, -51.9253, 'country', 215300000, 'BR'),
            'Canada': GeographicLocation('Canada', 56.1304, -106.3468, 'country', 38200000, 'CA'),
            'South Korea': GeographicLocation('South Korea', 35.9078, 127.7669, 'country', 51800000, 'KR'),
            'Australia': GeographicLocation('Australia', -25.2744, 133.7751, 'country', 25700000, 'AU'),
            'Spain': GeographicLocation('Spain', 40.4637, -3.7492, 'country', 47400000, 'ES'),
            'Mexico': GeographicLocation('Mexico', 23.6345, -102.5528, 'country', 128900000, 'MX'),
            'Indonesia': GeographicLocation('Indonesia', -0.7893, 113.9213, 'country', 273500000, 'ID'),
            'Netherlands': GeographicLocation('Netherlands', 52.1326, 5.2913, 'country', 17400000, 'NL'),
            'Saudi Arabia': GeographicLocation('Saudi Arabia', 23.8859, 45.0792, 'country', 34900000, 'SA'),
            'Turkey': GeographicLocation('Turkey', 38.9637, 35.2433, 'country', 84300000, 'TR'),
            'Switzerland': GeographicLocation('Switzerland', 46.8182, 8.2275, 'country', 8700000, 'CH'),
            'Poland': GeographicLocation('Poland', 51.9194, 19.1451, 'country', 37900000, 'PL'),
            'Argentina': GeographicLocation('Argentina', -38.4161, -63.6167, 'country', 45300000, 'AR'),
            'Norway': GeographicLocation('Norway', 60.4720, 8.4689, 'country', 5400000, 'NO'),
            'Sweden': GeographicLocation('Sweden', 60.1282, 18.6435, 'country', 10400000, 'SE'),
            'Belgium': GeographicLocation('Belgium', 50.5039, 4.4699, 'country', 11600000, 'BE'),
            'Israel': GeographicLocation('Israel', 31.0461, 34.8516, 'country', 9700000, 'IL'),
            'UAE': GeographicLocation('UAE', 23.4241, 53.8478, 'country', 9900000, 'AE'),
            'Singapore': GeographicLocation('Singapore', 1.3521, 103.8198, 'country', 5900000, 'SG'),
            'Malaysia': GeographicLocation('Malaysia', 4.2105, 101.9758, 'country', 32700000, 'MY'),
            'South Africa': GeographicLocation('South Africa', -30.5595, 22.9375, 'country', 59300000, 'ZA'),
            'Egypt': GeographicLocation('Egypt', 26.0963, 29.9870, 'country', 104300000, 'EG'),
            'Thailand': GeographicLocation('Thailand', 15.8700, 100.9925, 'country', 69800000, 'TH'),
            'Philippines': GeographicLocation('Philippines', 12.8797, 121.7740, 'country', 109600000, 'PH'),
            'Vietnam': GeographicLocation('Vietnam', 14.0583, 108.2772, 'country', 97300000, 'VN'),
            'Pakistan': GeographicLocation('Pakistan', 30.3753, 69.3451, 'country', 225200000, 'PK'),
            'Bangladesh': GeographicLocation('Bangladesh', 23.6850, 90.3563, 'country', 165000000, 'BD'),
            'Ukraine': GeographicLocation('Ukraine', 48.3794, 31.1656, 'country', 41700000, 'UA'),
            'Iran': GeographicLocation('Iran', 32.4279, 53.6880, 'country', 85000000, 'IR'),
            'Iraq': GeographicLocation('Iraq', 33.2232, 43.6793, 'country', 40000000, 'IQ'),
            'Afghanistan': GeographicLocation('Afghanistan', 33.9391, 67.7100, 'country', 38900000, 'AF'),
            'Colombia': GeographicLocation('Colombia', 4.5709, -74.2973, 'country', 50900000, 'CO'),
            'Chile': GeographicLocation('Chile', -35.6751, -71.5430, 'country', 19200000, 'CL'),
            'Peru': GeographicLocation('Peru', -9.1900, -75.0152, 'country', 33000000, 'PE'),
            'Venezuela': GeographicLocation('Venezuela', 6.4238, -66.5897, 'country', 28400000, 'VE'),
            'Ecuador': GeographicLocation('Ecuador', -1.8312, -78.1834, 'country', 17700000, 'EC'),
            'Bolivia': GeographicLocation('Bolivia', -16.2902, -63.5887, 'country', 11700000, 'BO'),
            'Paraguay': GeographicLocation('Paraguay', -23.4425, -58.4438, 'country', 7150000, 'PY'),
            'Uruguay': GeographicLocation('Uruguay', -32.5228, -55.7658, 'country', 3480000, 'UY'),
            'Cuba': GeographicLocation('Cuba', 21.5218, -77.7812, 'country', 11300000, 'CU'),
            'Haiti': GeographicLocation('Haiti', 18.9712, -72.2852, 'country', 11400000, 'HT'),
            'Dominican Republic': GeographicLocation('Dominican Republic', 18.7357, -70.1627, 'country', 10900000, 'DO'),
            'Jamaica': GeographicLocation('Jamaica', 18.1096, -77.2975, 'country', 2960000, 'JM'),
            'Trinidad and Tobago': GeographicLocation('Trinidad and Tobago', 10.6918, -61.2225, 'country', 1400000, 'TT'),
            'Barbados': GeographicLocation('Barbados', 13.1939, -59.5432, 'country', 287000, 'BB'),
        }

    def extract_geographic_features(self, title: str, description: str = "", entities: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Extract geographic features from article content.

        Args:
            title: Article title
            description: Article description/content
            entities: Extracted named entities

        Returns:
            Dictionary with geographic features and locations
        """
        text = f"{title} {description}".lower()

        # Extract locations from entities
        entity_locations = self._extract_locations_from_entities(entities or [])

        # Extract locations from text
        text_locations = self._extract_locations_from_text(text)

        # Combine and deduplicate
        all_locations = entity_locations + text_locations
        unique_locations = self._deduplicate_locations(all_locations)

        # Create geographic context
        geo_context = {
            'locations': unique_locations,
            'primary_location': self._select_primary_location(unique_locations),
            'location_hierarchy': self._build_location_hierarchy(unique_locations),
            'regional_context': self._determine_regional_context(unique_locations),
            'geographic_scope': self._assess_geographic_scope(unique_locations)
        }

        return geo_context

    def _extract_locations_from_entities(self, entities: List[Dict[str, Any]]) -> List[GeographicLocation]:
        """Extract geographic locations from named entities."""
        locations = []

        for entity in entities:
            entity_type = entity.get('type', '')
            entity_text = entity.get('text', '').strip()

            if entity_type in ['LOCATION', 'GPE']:
                # Check major cities
                if entity_text in self.major_cities:
                    locations.append(self.major_cities[entity_text])

                # Check US states
                elif entity_text in self.us_states:
                    locations.append(self.us_states[entity_text])

                # Check countries
                elif entity_text in self.countries:
                    locations.append(self.countries[entity_text])

                # Try to find partial matches for cities (e.g., "New York City" -> "New York")
                else:
                    for city_name, city_loc in self.major_cities.items():
                        if city_name.lower() in entity_text.lower():
                            locations.append(city_loc)
                            break

        return locations

    def _extract_locations_from_text(self, text: str) -> List[GeographicLocation]:
        """Extract geographic locations from raw text content."""
        locations = []

        # Check for cities
        for city_name in self.major_cities.keys():
            if city_name.lower() in text:
                locations.append(self.major_cities[city_name])

        # Check for states
        for state_name in self.us_states.keys():
            if state_name.lower() in text:
                locations.append(self.us_states[state_name])

        # Check for countries
        for country_name in self.countries.keys():
            if country_name.lower() in text:
                locations.append(self.countries[country_name])

        return locations

    def _deduplicate_locations(self, locations: List[GeographicLocation]) -> List[GeographicLocation]:
        """Remove duplicate locations."""
        seen = set()
        unique_locations = []

        for location in locations:
            key = (location.name, location.location_type)
            if key not in seen:
                seen.add(key)
                unique_locations.append(location)

        return unique_locations

    def _select_primary_location(self, locations: List[GeographicLocation]) -> Optional[GeographicLocation]:
        """Select the most important location from the list."""
        if not locations:
            return None

        # Prioritize by location type and population
        priority_order = {'city': 3, 'state': 2, 'country': 1, 'region': 0}

        sorted_locations = sorted(locations, key=lambda loc: (
            priority_order.get(loc.location_type, 0),
            loc.population or 0
        ), reverse=True)

        return sorted_locations[0] if sorted_locations else None

    def _build_location_hierarchy(self, locations: List[GeographicLocation]) -> Dict[str, List[str]]:
        """Build hierarchical relationships between locations."""
        hierarchy = {
            'cities': [],
            'states': [],
            'countries': [],
            'regions': []
        }

        for location in locations:
            if location.location_type == 'city':
                hierarchy['cities'].append(location.name)
            elif location.location_type == 'state':
                hierarchy['states'].append(location.name)
            elif location.location_type == 'country':
                hierarchy['countries'].append(location.name)
            elif location.location_type == 'region':
                hierarchy['regions'].append(location.name)

        return hierarchy

    def _determine_regional_context(self, locations: List[GeographicLocation]) -> str:
        """Determine the regional context of the locations."""
        if not locations:
            return 'global'

        countries = [loc.country_code for loc in locations if loc.country_code]
        unique_countries = set(countries)

        if len(unique_countries) == 1:
            country = list(unique_countries)[0]
            if country == 'US':
                return 'us_domestic'
            else:
                return f'{country.lower()}_domestic'

        elif len(unique_countries) <= 3:
            return 'regional'

        else:
            return 'international'

    def _assess_geographic_scope(self, locations: List[GeographicLocation]) -> str:
        """Assess the geographic scope of the article."""
        if not locations:
            return 'unknown'

        city_count = sum(1 for loc in locations if loc.location_type == 'city')
        state_count = sum(1 for loc in locations if loc.location_type == 'state')
        country_count = sum(1 for loc in locations if loc.location_type == 'country')

        if city_count >= 3 or (city_count >= 1 and state_count >= 1):
            return 'local'
        elif state_count >= 2 or (city_count >= 1 and country_count >= 1):
            return 'regional'
        elif country_count >= 2:
            return 'national'
        elif country_count == 1:
            return 'international'
        else:
            return 'local'

    def calculate_geographic_similarity(
        self,
        geo1: Dict[str, Any],
        geo2: Dict[str, Any],
        max_distance_km: float = 500.0
    ) -> float:
        """
        Calculate geographic similarity between two articles.

        Args:
            geo1: Geographic features of first article
            geo2: Geographic features of second article
            max_distance_km: Maximum distance to consider similar

        Returns:
            Similarity score (0-1)
        """
        if not geo1.get('locations') or not geo2.get('locations'):
            return 0.0

        # Check regional context similarity
        regional_similarity = 1.0 if geo1.get('regional_context') == geo2.get('regional_context') else 0.3

        # Check geographic scope similarity
        scope_similarity = 1.0 if geo1.get('geographic_scope') == geo2.get('geographic_scope') else 0.5

        # Calculate location proximity
        proximity_score = 0.0
        max_proximity = 0.0

        for loc1 in geo1['locations']:
            for loc2 in geo2['locations']:
                if loc1.location_type == loc2.location_type:  # Only compare same types
                    distance = loc1.distance_to(loc2)
                    if distance <= max_distance_km:
                        proximity = 1.0 - (distance / max_distance_km)
                        proximity_score = max(proximity_score, proximity)
                        max_proximity = 1.0

        if max_proximity == 0:
            proximity_score = 0.0

        # Check location hierarchy overlap
        hierarchy1 = geo1.get('location_hierarchy', {})
        hierarchy2 = geo2.get('location_hierarchy', {})

        hierarchy_overlap = 0.0
        total_categories = 0

        for category in ['cities', 'states', 'countries']:
            set1 = set(hierarchy1.get(category, []))
            set2 = set(hierarchy2.get(category, []))
            if set1 or set2:
                overlap = len(set1.intersection(set2))
                union = len(set1.union(set2))
                if union > 0:
                    hierarchy_overlap += overlap / union
                total_categories += 1

        hierarchy_similarity = hierarchy_overlap / total_categories if total_categories > 0 else 0.0

        # Weighted combination
        final_similarity = (
            regional_similarity * 0.3 +
            scope_similarity * 0.2 +
            proximity_score * 0.3 +
            hierarchy_similarity * 0.2
        )

        return min(final_similarity, 1.0)


# Global instance
_geographic_extractor = None


def get_geographic_extractor() -> GeographicFeatureExtractor:
    """Get global geographic feature extractor instance."""
    global _geographic_extractor
    if _geographic_extractor is None:
        _geographic_extractor = GeographicFeatureExtractor()
    return _geographic_extractor


def extract_geographic_features(title: str, description: str = "", entities: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Convenience function to extract geographic features from article.

    Args:
        title: Article title
        description: Article description
        entities: Extracted entities

    Returns:
        Geographic features dictionary
    """
    extractor = get_geographic_extractor()
    return extractor.extract_geographic_features(title, description, entities)


def calculate_geographic_similarity(geo1: Dict[str, Any], geo2: Dict[str, Any], max_distance_km: float = 500.0) -> float:
    """
    Convenience function to calculate geographic similarity.

    Args:
        geo1: Geographic features of first article
        geo2: Geographic features of second article
        max_distance_km: Maximum distance to consider similar

    Returns:
        Similarity score (0-1)
    """
    extractor = get_geographic_extractor()
    return extractor.calculate_geographic_similarity(geo1, geo2, max_distance_km)
