# Quick Start: Using Claude Code for This Project

## 🚀 First Time Setup

### 1. Open Your Project in Claude Code

```bash
cd ~/Desktop/Academics/thesis_v2/

# Start Claude Code
claude-code

# Or if that doesn't work, open in VS Code first then use Claude Code extension
code .
```

### 2. Start Your First Session

In Claude Code, say:

```
Hi! I'm working on a DeFi lending data collection project. Please read 
CLAUDE_CODE_CONTEXT.md to understand the full project context.

Our immediate task is to test the block cache builder at 
scripts/build_block_cache.py to make sure it works correctly.

Can you run it for December 2024 and verify the output?
```

---

## 💬 How to Communicate with Claude Code

### ✅ Effective Prompts

**Task-oriented:**
```
"Build a parallel TVL collector that uses ThreadPoolExecutor with 5 workers,
loads block cache from data/cache/, and saves results to data/bronze/tvl/"
```

**Problem-solving:**
```
"The block cache is loading but the timestamps don't match the expected dates.
Can you debug why?"
```

**Exploratory:**
```
"Show me how the Aave V3 adapter works and explain the data structure it returns"
```

### ❌ Less Effective Prompts

**Too vague:**
```
"Make the code better"
```

**Too prescriptive:**
```
"Change line 42 to use a different variable name"
```

**No context:**
```
"Build a collector" 
(Better: reference the context doc and be specific about what to collect)
```

---

## 🔄 Typical Development Flow

### Pattern 1: Building New Code

```
You: "Build a parallel TVL collector. Requirements: [list requirements]
      See CLAUDE_CODE_CONTEXT.md for full context."

Claude Code: [writes scripts/collect_tvl_parallel.py]

Claude Code: [runs test with sample data]

Claude Code: "I've created the collector. It successfully collected data 
              for 5 CSUs. Ready to test with all 43?"

You: "Yes, but add more detailed logging so we can monitor progress"

Claude Code: [adds logging, tests again]

Claude Code: "Updated with logging. Here's sample output: [shows logs]"

You: "Perfect! Now commit this to git with message 'Add parallel TVL collector'"

Claude Code: [commits code]
```

### Pattern 2: Debugging Issues

```
You: "The collector is failing with RPC timeout errors on Polygon. 
      Can you add retry logic?"

Claude Code: [analyzes code, identifies issue]

Claude Code: "The timeout is happening because Polygon needs longer timeouts.
              I'll add exponential backoff retry logic."

Claude Code: [implements fix, tests]

Claude Code: "Fixed! Now retries up to 3 times with exponential backoff.
              Tested on Polygon and it works."
```

### Pattern 3: Understanding Existing Code

```
You: "Explain how the rate limiter in rpc_pool.py works"

Claude Code: [reads file, explains]

Claude Code: "The RateLimiter class ensures we don't exceed 10 calls/sec
              per key by tracking the time since last call and sleeping
              if needed. Here's how it works: [detailed explanation]"
```

---

## 📋 Session Checklist

### Start of Each Session

- [ ] Share `CLAUDE_CODE_CONTEXT.md` 
- [ ] Make sure `.env` is loaded (`source ../.env`)
- [ ] Explain the specific task clearly
- [ ] Mention any relevant constraints

### During Session

- [ ] Let Claude Code run and test code
- [ ] Provide feedback on outputs, not implementation
- [ ] Ask for explanations if design choices are unclear
- [ ] Check data quality manually when new data is generated

### End of Session

- [ ] Review all changes made
- [ ] Test outputs manually
- [ ] Commit working code to GitHub
- [ ] Note any issues for next session

---

## 🎯 Your Immediate Tasks with Claude Code

### Task 1: Test Block Cache Builder (30 mins)

**Prompt:**
```
Please read CLAUDE_CODE_CONTEXT.md for project context.

Our first task is to test the block cache builder at scripts/build_block_cache.py.

Run it for December 2024 with these chains: ethereum, arbitrum, base, optimism

Expected output: 4 JSON files in data/cache/ with date→block mappings for 
Dec 1-31 (31 entries each).

Verify:
1. Files are created correctly
2. Block numbers increase over time
3. Timestamps match expected dates
4. No RPC errors

If any issues, debug and fix them.
```

### Task 2: Build TVL Collector (2-3 hours)

**Prompt:**
```
Now build scripts/collect_tvl_parallel.py to collect TVL data.

Requirements:
- Use ThreadPoolExecutor with 5 workers
- Load block cache from data/cache/ (don't recompute)
- Use get_web3() from config/rpc_pool for RPC connections
- Call appropriate adapter from adapters/tvl/ based on CSU family
- Save bronze format to data/bronze/tvl/{csu_name}/{date}.json
- Add checkpoint file at data/checkpoint.json for resume capability
- Show progress (e.g., "Completed 150/1333 tasks")

Start by collecting just Dec 31 for 5 CSUs as a test, then scale up.

See CLAUDE_CODE_CONTEXT.md for bronze output format example.
```

### Task 3: Build Liquidation Collector (4-6 hours)

**Prompt:**
```
Build scripts/collect_liquidations_parallel.py for liquidation events.

Key difference from TVL: eth_getLogs is limited to 10 blocks per call.
Must chunk each day into ~720 windows (7200 blocks ÷ 10).

Requirements:
- Chunk each day into 10-block windows
- Parallelize chunks across workers
- Use appropriate adapter from adapters/liquidations/
- Save to data/bronze/liquidations/{csu_name}/{date}.json
- Checkpoint/resume critical (long-running)
- Progress monitoring

Start with 1 CSU, 1 day as test before scaling.

This is the expensive operation - see CLAUDE_CODE_CONTEXT.md for rate limit
concerns.
```

---

## 🔧 Common Issues & Solutions

### Issue: "Command not found: claude-code"

**Solution:**
```bash
# Use VS Code with Claude Code extension instead
code ~/Desktop/Academics/thesis_v2/
# Then use Claude Code panel in VS Code
```

### Issue: Claude Code doesn't have context

**Solution:**
```
"Please read CLAUDE_CODE_CONTEXT.md first"
```

### Issue: RPC errors during testing

**Solution:**
```bash
# Make sure .env is loaded
cd ~/Desktop/Academics/
source .env

# Verify keys loaded
echo $ALCHEMY_KEY_1
```

### Issue: Rate limiting errors

**Solution:**
Tell Claude Code: "We're hitting rate limits. Can you add exponential backoff
and/or reduce the number of parallel workers?"

---

## 📊 Progress Tracking

After each session, update this:

```
Session 1: Block Cache
- [x] Tested block cache builder
- [x] Verified output format
- [ ] Any issues: _______________

Session 2: TVL Collector  
- [ ] Built collector
- [ ] Tested with 5 CSUs
- [ ] Tested with all 43 CSUs
- [ ] Any issues: _______________

Session 3: Liquidation Collector
- [ ] Built collector
- [ ] Tested with 1 CSU, 1 day
- [ ] Scaled to priority CSUs
- [ ] Any issues: _______________
```

---

## 🎓 Learning Tips

**Let Claude Code explore:**
```
"Show me how the existing adapters work before we build new code"
```

**Ask for explanations:**
```
"Explain why you chose ThreadPoolExecutor over ProcessPoolExecutor"
```

**Request improvements:**
```
"This works but error handling could be better. Can you improve it?"
```

**Get estimates:**
```
"How long will collecting all 43 CSUs take with current rate limiting?"
```

---

## ✅ Success Criteria

You'll know things are working when:

1. **Block cache builder:**
   - Creates 4 JSON files without errors
   - Each has 31 date→block entries
   - Timestamps match expected dates

2. **TVL collector:**
   - Collects all 43 CSUs × 31 days = 1,333 files
   - No RPC errors
   - Bronze format matches spec
   - Takes ~1 hour with rate limiting

3. **Liquidation collector:**
   - Handles 10-block chunking correctly
   - Checkpoint/resume works
   - No missed events
   - Takes ~8-12 hours for priority CSUs

---

## 🚀 Ready to Start!

Open Claude Code and begin with Task 1 (block cache testing).

**First prompt:**
```
Hi! Please read CLAUDE_CODE_CONTEXT.md to understand this DeFi data 
collection project.

Our first task is to test scripts/build_block_cache.py for December 2024.
Can you run it and verify it works correctly?
```

Good luck! 🎯
