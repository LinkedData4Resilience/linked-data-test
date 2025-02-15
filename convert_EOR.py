# This file is used to convert the structered data of the Eyes On Russia dataset to linked data 


import csv
import time
from bs4 import BeautifulSoup
from rdflib import FOAF, RDFS, Graph, Literal, Namespace, RDF, URIRef
from rdflib.namespace import XSD, RDFS, RDF
import json
from datetime import datetime
import urllib.parse
import requests
import validators
import requests

from rdflib.namespace import NamespaceManager


# username for GeoNames
fuser = open("userinfo.txt","r")
username = fuser.readline().strip()

with open("datasets/city_coordinates.json") as fresult:
    existing_results = json.load(fresult)

# Define the GeoNames API URL and username
GEONAMES_API_URL = 'http://api.geonames.org/searchJSON'
GEONAMES_USERNAME = username

# Define namespaces
# Registratie: linked4resilience.eu
l4r_eor_namespace_event = Namespace("https://linked4resilience.eu/data/EOR/April2023/event/")
l4r_eor_namespace_location = Namespace("https://linked4resilience.eu/data/EOR/April2023/location/")
l4r_eor_namespace_geo = Namespace("https://linked4resilience.eu/data/EOR/April2023/geo/")
l4r_o_namespace = Namespace("https://linked4resilience.eu/ontology/")


sem_namespace = Namespace("http://semanticweb.cs.vu.nl/2009/11/sem/")

gno_namespace = Namespace('http://www.geonames.org/ontology#')
gni_namespace = Namespace ('https://sws.geonames.org/')


sdo_namespace = Namespace("https://schema.org/")

# Create an RDF graph
rdf_graph = Graph()

# Bind namespaces
# Appraoch 1
rdf_graph.bind("l4revent", l4r_eor_namespace_event)
rdf_graph.bind("l4rlocation", l4r_eor_namespace_location)
rdf_graph.bind("l4rgeo", l4r_eor_namespace_geo)
rdf_graph.bind("l4ro", l4r_o_namespace)

rdf_graph.bind("xsd", XSD)
rdf_graph.bind('gno', gno_namespace)
rdf_graph.bind('gni', gni_namespace)
rdf_graph.bind('sem', sem_namespace)
rdf_graph.bind('sdo', sdo_namespace)
rdf_graph.bind('rdfs', RDFS)

#counting entries
num_entry = 0
num_vio = 0
num_date = 0
num_label = 0
num_postalCode = 0
num_country = 0
num_coordinates = 0

num_prov = 0
# cities
num_city = 0
num_cities_original_EoR = 0
cities_not_found = set()
# social media content
num_url = 0
num_validated_url = 0
num_403_url = 0
num_404_url = 0

event_id = 1
location_id = 1
geo_id = 1



# accesing enrichment files 

with open('datasets/original_ukrainian_geoname_uri_mappings.json', 'r') as original_ukrainian_cities:
    original_geoname_uri_mappings = json.load(original_ukrainian_cities)
    with open('datasets/extended-ukrainian-geoname-uri-mappings.json', 'r', encoding='utf-8') as extended_ukrainian_cities:
        extended_geoname_uri_mappings = json.load(extended_ukrainian_cities)

        original_geoname_uri_mappings.update(extended_geoname_uri_mappings)
        geoname_uri_mappings = original_geoname_uri_mappings
    with open("french_city_dict.json", "r") as f_file:
        french_city_dict = json.load(f_file)


    with open("ukrainian_city_dict.json", "r") as uk_file:
        ukrainian_city_dict = json.load(uk_file)

    with open("dutch_city_dict.json", "r") as d_file:
        dutch_city_dict = json.load(d_file)
    with open("english_city_dict.json", "r") as e_file:
        english_city_dict = json.load(e_file)

    # Open the JSON file
    with open("datasets\enriched_original_EOR-2023-04-30.json") as fjson:
        data = json.load(fjson)

        
        
        # Loop through the features in the JSON file
        for feature in data['features']:
            # print ('event id ', event_id)

            # Ensure all events are in Ukraine
            if feature["properties"].get("country") == "Ukraine":

                num_entry +=1
                event_URI = l4r_eor_namespace_event + str(event_id).zfill(8)
                comment_in_preparation = ''

            # Conversion of the attributes

                # processing the date
                if feature['properties'].get('verifiedDate'):

                    verified_date_str = feature['properties']['verifiedDate']
                    verified_date_obj = datetime.fromisoformat(verified_date_str)
                    verified_date_str_no_time = verified_date_obj.date().isoformat()


                    rdf_graph.add((URIRef(event_URI), URIRef('http://purl.org/dc/terms/date'), Literal(verified_date_str_no_time, datatype=XSD.date)))
                    num_date += 1
                # cooridantes conversion 
                if feature['geometry'].get('coordinates'):
                    num_coordinates += 1
                    lng, lat = feature["geometry"]["coordinates"]
 

                    # event schema:location 
                    location_URI = l4r_eor_namespace_location + str(location_id).zfill(8)
                    location_id += 1
                    rdf_graph.add((URIRef(event_URI), sdo_namespace.location, URIRef(location_URI))) # updated from lat

                    geo_URI = l4r_eor_namespace_geo + str(geo_id).zfill(8)
                    geo_id += 1
                    rdf_graph.add((URIRef(location_URI), RDF.type, sdo_namespace.Place)) #
                    rdf_graph.add((URIRef(location_URI), sdo_namespace.geo, URIRef(geo_URI))) #

                    rdf_graph.add((URIRef(geo_URI), RDF.type, sdo_namespace.GeoCoordinates)) #

                    rdf_graph.add((URIRef(geo_URI), sdo_namespace.latitude, Literal(lat, datatype=XSD.float))) # updated from lat

                    rdf_graph.add((URIRef(geo_URI), sdo_namespace.longitude, Literal(lng, datatype=XSD.float))) # updated from lng


                    # rdf_graph.add((URIRef(event_URI), sdo_namespace.latitude, Literal(lat, datatype=XSD.float))) # updated from lat


                    # rdf_graph.add((URIRef(event_URI), sdo_namespace.longitude, Literal(lng, datatype=XSD.float))) # updated from lng



                if feature["properties"].get("violenceLevel"):
                    
                    comment_in_preparation += 'Editors of the Eyes on Russia project assigned a violence level to this event as ' + str(feature['properties']['violenceLevel']) + '. '
                    num_vio += 1

                if feature["properties"].get("description"):
                    rdf_graph.add((URIRef(event_URI), RDFS.label, Literal(feature["properties"]['description'], lang="en")))
                    num_label += 1
                else:
                    rdf_graph.add((URIRef(event_URI), RDFS.label, Literal('no description', lang="en")))

                if feature.get("postalCode"):
                    rdf_graph.add((URIRef(event_URI), sdo_namespace.postalCode, Literal(feature['postalCode'])))
                    #print ('\thas postalcode: ', Literal(feature['postalCode']))
                    num_postalCode +=1

                # if 'postalCode' not in feature:
                #     geonames_url = f'http://api.geonames.org/findNearbyPostalCodesJSON?lat={lat}&lng={lng}&username={username}'
                #     response = requests.get(geonames_url).json()
                    
                    # if 'postalCode' in response['postalCodes'][0]:
                    #     postalCode = response['postalCodes'][0]['postalCode']
                    #     rdf_graph.add((URIRef(event_URI), sdo_namespace.postalCode, Literal(postalCode)))
                    #     num_postalCode +=1


                if feature["properties"].get("country"):
                    country_name = feature['properties']['country']
                    # print ('\tcountry: ', country_name)
                    if country_name in geoname_uri_mappings:
                        country_uri = URIRef(geoname_uri_mappings[country_name])
                        rdf_graph.add((URIRef(event_URI), l4r_o_namespace.addressCountry, country_uri))
                        # print ('\tCountry URI: ', country_uri)
                        num_country += 1
                    else:
                        rdf_graph.add((URIRef(event_URI), l4r_o_namespace.addressCountry, Literal(feature["properties"]["country"])))
                        print ('ERROR: the URI is not in the saved Geonames mapping: ', country_name)
                        print ('this event has URI: ', event_URI)

                if feature["properties"].get("province"):
                    prov_name = feature['properties']['province']
                    if prov_name in geoname_uri_mappings:
                        prov_uri = URIRef(geoname_uri_mappings[prov_name])
                        rdf_graph.add((URIRef(event_URI), l4r_o_namespace.addressRegion, prov_uri))
                        num_prov += 1
                    else:
                        rdf_graph.add((URIRef(event_URI), l4r_o_namespace.addressRegion, Literal(feature["properties"]["province"])))
                        print ('ERROR: the URI is not in the saved Geonames mapping: ', prov_name)
                        print ('this event has URI: ', event_URI)

                if feature["properties"].get("city"):
                    num_cities_original_EoR += 1
                    city_name = feature['properties']['city']
                    if city_name in geoname_uri_mappings:
                        city_uri = URIRef(geoname_uri_mappings[city_name])
                        rdf_graph.add((URIRef(event_URI), l4r_o_namespace.addressCity, city_uri))
                        
                        geoname_id = geoname_uri_mappings[city_name].split("/")[-2]
                        if geoname_id in french_city_dict:
                            rdf_graph.add((URIRef(event_URI), l4r_o_namespace.cityName, Literal(french_city_dict[geoname_id], lang="fr")))
                        if geoname_id in ukrainian_city_dict:
                            rdf_graph.add((URIRef(event_URI), l4r_o_namespace.cityName, Literal(ukrainian_city_dict[geoname_id], lang="uk")))
                        if geoname_id in dutch_city_dict:
                            rdf_graph.add((URIRef(event_URI), l4r_o_namespace.cityName, Literal(dutch_city_dict[geoname_id], lang="nl"))) 
                        if geoname_id in english_city_dict:
                            rdf_graph.add((URIRef(event_URI), l4r_o_namespace.cityName, Literal(english_city_dict[geoname_id], lang="en")))          
                        num_city += 1
                    else:
                        for c in existing_results:

                            if feature["geometry"]["coordinates"] == c['coordinates']:
                                city_uri = URIRef(c['URI'])
                                rdf_graph.add((URIRef(event_URI), l4r_o_namespace.addressCity, city_uri))
                                
                                geoname_id = c['URI'].split("/")[-2]
                                if geoname_id in french_city_dict:
                                    rdf_graph.add((URIRef(event_URI), l4r_o_namespace.cityName, Literal(french_city_dict[geoname_id], lang="fr")))
                                if geoname_id in ukrainian_city_dict:
                                    rdf_graph.add((URIRef(event_URI), l4r_o_namespace.cityName, Literal(ukrainian_city_dict[geoname_id], lang="uk")))
                                if geoname_id in dutch_city_dict:
                                    rdf_graph.add((URIRef(event_URI), l4r_o_namespace.cityName, Literal(dutch_city_dict[geoname_id], lang="nl")))
                                if geoname_id in english_city_dict:
                                    rdf_graph.add((URIRef(event_URI), l4r_o_namespace.cityName, Literal(english_city_dict[geoname_id], lang="en")))          
                                num_city += 1
                                break


                if 'city' not in feature["properties"]: 
                    for c in existing_results:

                            if feature["geometry"]["coordinates"] == c['coordinates']:
                                city_uri = URIRef(c['URI'])
                                rdf_graph.add((URIRef(event_URI), l4r_o_namespace.addressCity, city_uri))
                                
                                geoname_id = c['URI'].split("/")[-2]
                                if geoname_id in french_city_dict:
                                    rdf_graph.add((URIRef(event_URI), l4r_o_namespace.cityName, Literal(french_city_dict[geoname_id], lang="fr")))
                                if geoname_id in ukrainian_city_dict:
                                    rdf_graph.add((URIRef(event_URI), l4r_o_namespace.cityName, Literal(ukrainian_city_dict[geoname_id], lang="uk")))    
                                if geoname_id in dutch_city_dict:
                                    rdf_graph.add((URIRef(event_URI), l4r_o_namespace.cityName, Literal(dutch_city_dict[geoname_id], lang="nl")))
                                if geoname_id in english_city_dict:
                                    rdf_graph.add((URIRef(event_URI), l4r_o_namespace.cityName, Literal(english_city_dict[geoname_id], lang="en")))          
                                num_city += 1
                                break
                                
                for category in feature['properties']['categories']:
                    # Eyes on Russia provides some extra information as the category of the event. We decide to keep this in the comment
                    comment_in_preparation += 'According to Eyes on Russia, this event is of type '+ category +'. '
                    # print ('comment: ', comment_in_preparation + 'The type of event could be ' +category)
                
                if feature['properties'].get('url'):
                    social_media_content_url = feature["properties"]['url']
                    rdf_graph.add((URIRef(event_URI), sdo_namespace.url, Literal(social_media_content_url, datatype=XSD.anyURI)))
                    num_url += 1      

                # Create a URI for the event using the event ID 
                rdf_graph.add((URIRef(event_URI), RDF.type, sem_namespace.Event))
                if comment_in_preparation != '':
                    rdf_graph.add((URIRef(event_URI), RDFS.comment, Literal(comment_in_preparation, lang="en")))
                
                # increment ID
                event_id += 1

# print the number of entries 
print ('#Entry ', num_entry)
print ('#violence level ', num_vio)
print ('#rdfs:label ', num_label)
print ('#postalCode ', num_postalCode)
print ('#country', num_country)
print ('#date ', num_date)
print ('#coordinates ', num_coordinates)
print ('#province ', num_prov)
print ('num_cities_original_EoR ', num_cities_original_EoR)
print ('#city (found in Geonames)', num_city)
print ('#(unique) cities not found ', len(cities_not_found))
# for r in cities_not_found:
#      print (r)
print ('count URL: ', num_url)
print ('valid URL: ', num_validated_url)
print ('403 URL: ', num_403_url)
print ('404 URL: ', num_404_url)
sorted_triples = sorted(rdf_graph, key=lambda triple: triple[0])
sorted_graph = Graph()
sorted_graph += sorted_triples

# serialize the sorted graph to a string in RDF/XML format
serialized = sorted_graph.serialize(format="ttl")
with open("converted_EOR-2023-04-30.ttl", "wb") as f:
        f.write(serialized.encode('utf-8'))
