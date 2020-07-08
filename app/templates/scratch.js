    Object.keys(finished).forEach(function(key) {
      for (var act of finished[key]) {
        var coordinates = L.Polyline.fromEncoded(act.poyline).getLatLngs();
        L.polyline(

            coordinates,
            {
                color: 'blue',
                weight: 2,
                opacity: .7,
                lineJoin: 'round'
            }
        ).addTo(map);
      }
    }

    Object.keys(finished).forEach(function(key) {
      var mydiv = document.createElement("myDiv");
      var aTag = document.createElement('a');
      aTag.innerText = key.name + "\n";
      mydiv.appendChild(aTag);

      i = 1
      for (var act of finished[key]) {
        var aTag = document.createElement('a');
        aTag.setAttribute('href',"https://strava.com/activities/" + act.activity_id);
        aTag.setAttribute('target', "_blank");
        aTag.innerText = i + "\n";
        i += 1
        mydiv.appendChild(aTag);
        }

      L.marker([key.lat, key.lon).addTo(map).bindPopup(mydiv);
    }