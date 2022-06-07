using Newtonsoft.Json;
using System.Collections.Generic;

namespace SerendipityWebApp.Models
{
    public class Playlist
    {
        [JsonProperty("pid")]
        public int Pid { get; set; }
        [JsonProperty("_id")]
        public string Id { get; set; }
        [JsonProperty("name")]
        public string Name { get; set; }
        [JsonProperty("tracks")]
        public List<Track> Tracks { get; set; }
        [JsonProperty("track_ids")]
        public List<string> TrackIds { get; set; }
        [JsonProperty("description")]
        public string Description { get; set; }

        public Playlist()
        {
            Tracks = new List<Track>();
            TrackIds = new List<string>();
        }
    }
}