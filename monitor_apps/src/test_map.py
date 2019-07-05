import folium


m = folium.Map(location=[52.720347, 58.665166], zoom_start=16)
tooltip = 'info'
folium.Marker([52.720347, 58.665166], popup='<i>хлороводород</i>', tooltip=tooltip).add_to(m)
m.save('index.html')