from pygris import blocks, tracts, block_groups
from libpysal import weights
import networkx as nx

def generate_graph_census(census_unit='tracts',
                          state='NY',
                          counties=['New York','Bronx','Kings','Queens','Richmond'],
                          weight_scheme='rook',
                          remove_high_degree_nodes=False,
                          remove_long_edges=False,
                          remove_zeropop=False,
                          remove_parks=False,
                          tresh_degree=9,
                          tresh_edgelength=2_000,
                          tresh_parkarea=0.75,
                          tresh_population=1):
    
    #Collect the full census geography data:
    assert census_unit.lower() in ['tracts', 'blocks', 'block groups', 'blockgroups']
    if census_unit.lower() == 'tracts':
        census_gdf_raw = tracts(state=state, county=counties)
    elif census_unit.lower() == 'blocks':
        census_gdf_raw = blocks(state=state, county=counties)
    elif census_unit.lower() == 'block groups' or census_unit.lower() == 'blockgroups':
        census_gdf_raw = block_groups(state=state, county=counties)
        
    #Get the weights:
    assert weight_scheme.lower() in ['rook', 'queen']
    if weight_scheme.lower() == 'rook':
        spatial_weights = weights.Rook.from_dataframe(census_gdf_raw, silence_warnings=True)
    elif weight_scheme.lower() == 'queen':
        spatial_weights = weights.Queen.from_dataframe(census_gdf_raw, silence_warnings=True)
        
    #Convert weights to graph:
    graph_raw = spatial_weights.to_networkx()
    
    #Trim the graph from outliers:
    if remove_high_degree_nodes: graph_raw = trim_graph_degree(graph_raw, tresh_degree)
    if remove_long_edges: graph_raw = trim_graph_edge(graph_raw, census_gdf_raw, tresh_edgelength)
    if remove_parks: graph_raw = trim_graph_parks(graph_raw, census_gdf_raw, tresh_parkarea)
    if remove_zeropop: graph_raw = trim_graph_pop(graph_raw, census_gdf_raw, tresh_population)
    
    #Collect the largest connected component:
    graph_largest_component = max(nx.connected_components(graph_raw), key=len)
    graph = graph_raw.subgraph(graph_largest_component).copy()
    
    #Filter the gdf:
    census_gdf = census_gdf_raw.iloc[list(graph.nodes())].reset_index(drop=True)
    final_graph = nx.convert_node_labels_to_integers(graph)
    
    return census_gdf, final_graph, census_gdf_raw