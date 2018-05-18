# -*- coding: utf-8 -*-
"""
Created on Tue May  8 17:48:55 2018

@author: roland

inspired by https://github.com/paulgb/gtfs-gexf/blob/master/transform.py
"""

import networkx as nx
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from csv import DictReader
from itertools import groupby
import cartopy.feature as cfeature

    
DATA_ROOT='C:\\Users\\rolan\\Downloads\\SydneyTrains\\'
TRIPS_FILE = f'{DATA_ROOT}trips.txt'
ROUTES_FILE = f'{DATA_ROOT}routes.txt'
STOPS_FILE = f'{DATA_ROOT}stops.txt'

INCLUDE_AGENCIES=['NSWTrainLink']

IGNORE_ROUTE=['RTTA_DEF', #out of service
              'RTTA_REV',  #revenue train (charter)
              'BL_1b','BL_1c','BL_1d','BL_1e']

G = nx.MultiGraph()

#trips_csv = DictReader(open(f'{DATA_ROOT}trips.txt','r'))
#stops_csv = DictReader(open(f'{DATA_ROOT}stops.txt','r'))
#stop_times_csv = DictReader(open(f'{DATA_ROOT}stop_times.txt','r'))
#routes_csv = DictReader(open(f'{DATA_ROOT}routes.txt','r'))


def get_stop_id(stop_id):
    """ translate stop_id to parent_stop_id 
        if available
    """
    if STOPS[stop_id]['parent_station'] == '':
        return stop_id
    else:
        return STOPS[stop_id]['parent_station']


def add_stop_to_graph(G, stop_id):
    """ add stop as new node to graph
    """
    #lookup details of the stop (parent stop if available)
    node = STOPS[get_stop_id(stop_id)]

    if node['stop_id'] not in G.nodes:
        G.add_node(node['stop_id'], 
                   stop_name = node['stop_name'], 
                   stop_lon = node['stop_lon'], 
                   stop_lat = node['stop_lat'])
    return G

def add_edge_to_graph(G, from_id, to_id, route_short_name):
    """ add edge to graph 
        adding the route short name as a key
        if the edge and key exist, increment the count
    """
    edge = G.get_edge_data(get_stop_id(from_id), get_stop_id(to_id),route_short_name, default = 0)
    if edge == 0:
        G.add_edge(get_stop_id(from_id), get_stop_id(to_id), 
                   key=route_short_name,
                   count=1)
    else:
        G.add_edge(get_stop_id(from_id), get_stop_id(to_id), 
                   key=route_short_name,
                   count=edge['count']+1)
            

def load_routes(filename):
    """ include only routes from agencies we are interested in
    """
    routes_csv = DictReader(open(filename,'r'))
    routes_dict = dict()
    for route in routes_csv:
        if (route['agency_id'] in INCLUDE_AGENCIES and 
            route['route_id'] not in IGNORE_ROUTE ):
            
            routes_dict[route['route_id']] = route
    print ('routes', len(routes_dict))
    return routes_dict


def load_trips(filename, routes_dict):
    """ load trips from file
        only include trips on routes we are interested in
    """
    trips_csv = DictReader(open(filename,'r'))
    trips_dict = dict()
    for trip in trips_csv:
        if trip['route_id'] in routes_dict:
            trip['color'] = routes_dict[trip['route_id']]['route_color']
            trip['route_short_name']=routes_dict[trip['route_id']]['route_short_name']
            trips_dict[trip['trip_id']] = trip
    print ('trips', len(trips_dict))
    return trips_dict

    
def load_stops(filename):
    stops_csv = DictReader(open(filename,'r'))
    stops_dict = dict()
    for stop in stops_csv:
        stops_dict[stop['stop_id']] = stop
    print ('stops', len(stops_dict))   
    return stops_dict


# ==============================================


ROUTES = load_routes(filename=ROUTES_FILE)
TRIPS = load_trips(filename=TRIPS_FILE, routes_dict=ROUTES)
STOPS = load_stops(filename=STOPS_FILE)

stop_times_csv = DictReader(open(f'{DATA_ROOT}stop_times.txt','r'))

stops = set()
edges = dict()
for trip_id, stop_time_iter in groupby(stop_times_csv, lambda stop_time: stop_time['trip_id']):
    if trip_id in TRIPS:
        trip = TRIPS[trip_id]
        prev_stop = next(stop_time_iter)['stop_id']
        stops.add(prev_stop)
        for stop_time in stop_time_iter:
            stop = stop_time['stop_id']
            edge = (prev_stop, stop)
            edges[edge] = trip['route_short_name']
            stops.add(stop)
            prev_stop = stop
print ('stops', len(stops))
print ('edges', len(edges))

for stop_id in STOPS:
    if stop_id in stops:
       add_stop_to_graph(G, stop_id)
print('Nodes:', G.number_of_nodes() )
        
for (start_stop_id, end_stop_id), route_short_name in edges.items():
    add_edge_to_graph(G, 
                      from_id = start_stop_id, 
                      to_id = end_stop_id, 
                      route_short_name=route_short_name)
print('Edges:', G.number_of_edges() )








deg = nx.degree(G)
labels = {stop_id: G.node[stop_id]['stop_name'] if deg[stop_id] >= 0 else ''
          for stop_id in G.nodes}

pos = {stop_id: (G.node[stop_id]['stop_lon'], G.node[stop_id]['stop_lat'])
       for stop_id in G.nodes}


# lon/lat data is in PlateCarree projection
data_crs = ccrs.PlateCarree()

fig = plt.figure(figsize=(20,20))
ax = plt.axes(projection=ccrs.PlateCarree()) #central_longitude=151
#ax.set_extent((150, 155, -35, -32))

nx.draw_networkx(G
                 ,ax=ax
#                 ,labels=labels
                 ,pos=pos
                 ,node_size=2
                 ,transform=data_crs
                )
#ax.set_axis_off()

plt.show()
