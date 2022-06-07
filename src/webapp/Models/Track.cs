using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace SerendipityWebApp.Models
{
    public class Track
    {
        public string Id { get; set; }
        public string Name { get; set; }
        public Album Album { get; set; }
        public Artist Artist { get; set; }
    }
}
