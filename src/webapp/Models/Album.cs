using Newtonsoft.Json;

namespace SerendipityWebApp.Models
{
    public class Album
    {
        public string Id { get; set; }
        public string Name { get; set; }
        public string ArtistId { get; set; }

        [JsonProperty("release_date")]
        public string ReleaseDate { get; set; }
    }
}
