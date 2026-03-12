using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using ParagonWebAPI;
using ParagonWebAPI.Types;

namespace ParagonWebAPI.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    [Authorize]
    public class JsonChunksController : ControllerBase
    {
        private readonly MongoContext _context;

        public JsonChunksController(MongoContext context)
        {
            _context = context;
        }

        // GET: api/JsonChunks
        [HttpGet]
        public async Task<ActionResult<IEnumerable<JsonChunk>>> GetJsonChunks()
        {
            return await _context.Chunks.ToListAsync();
        }

        // GET: api/JsonChunks/5
        [HttpGet("{id}")]
        public async Task<ActionResult<JsonChunk>> GetJsonChunk(string id)
        {
            var jsonChunk = await _context.Chunks.FindAsync(id);

            if (jsonChunk == null)
            {
                return NotFound();
            }

            return jsonChunk;
        }

        // PUT: api/JsonChunks/5
        // To protect from overposting attacks, see https://go.microsoft.com/fwlink/?linkid=2123754
        [HttpPut("{id}")]
        public async Task<IActionResult> PutJsonChunk(string id, JsonChunk jsonChunk)
        {
            if (id != jsonChunk.ID)
            {
                return BadRequest();
            }

            _context.Entry(jsonChunk).State = EntityState.Modified;

            try
            {
                await _context.SaveChangesAsync();
            }
            catch (DbUpdateConcurrencyException)
            {
                if (!JsonChunkExists(id))
                {
                    return NotFound();
                }
                else
                {
                    throw;
                }
            }

            return NoContent();
        }

        // POST: api/JsonChunks
        // To protect from overposting attacks, see https://go.microsoft.com/fwlink/?linkid=2123754
        [HttpPost("uploadChunk")]
        public async Task<ActionResult<JsonChunk>> UploadChunk(JsonChunk jsonChunk)
        {
            _context.Chunks.Add(jsonChunk);
            await _context.SaveChangesAsync();

            if(jsonChunk.ChunkNumber == jsonChunk.TotalChunks)
            {
                var IDToLook = jsonChunk.ID;
                var allChunks = _context.Chunks
                    .Where(c => c.ID == IDToLook)
                    .OrderBy(c => c.ChunkNumber)
                    .Select(c => c.Data);

                var fullJson = string.Concat(allChunks);
                var assembledChunks = new JsonFull(fullJson);
                _context.AssembledChunks.Add(assembledChunks);

                await _context.SaveChangesAsync();

                var chunksToDelete = await _context.Chunks.Where(c => c.ID != IDToLook).ToListAsync();

                if (chunksToDelete.Any())
                {
                    _context.Chunks.RemoveRange(chunksToDelete);

                    await _context.SaveChangesAsync();

                }
            }

            return CreatedAtAction("GetJsonChunk", new { id = jsonChunk.ID }, jsonChunk);
        }

        // DELETE: api/JsonChunks/5
        [HttpDelete("{id}")]
        public async Task<IActionResult> DeleteJsonChunk(string id)
        {
            var jsonChunk = await _context.Chunks.FindAsync(id);
            if (jsonChunk == null)
            {
                return NotFound();
            }

            _context.Chunks.Remove(jsonChunk);
            await _context.SaveChangesAsync();

            return NoContent();
        }

        private bool JsonChunkExists(string id)
        {
            return _context.Chunks.Any(e => e.ID.Equals(id));
        }
    }
}
