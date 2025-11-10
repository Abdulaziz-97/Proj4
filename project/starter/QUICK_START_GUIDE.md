# UDA-Hub Quick Start Guide

## ✅ What You Have (Ready to Use)

### **Core Infrastructure** 
```
✅ agentic/state.py              - Complete state management
✅ agentic/memory_manager.py     - Complete memory system  
✅ agentic/tools/                - 13 tools fully implemented
   ├── db_manager.py             - Database connections
   ├── knowledge_tools.py        - 3 knowledge base tools
   ├── account_tools.py          - 5 account management tools
   ├── memory_tools.py           - 5 memory & ticket tools
   ├── __init__.py               - Tool package initialization
   └── README.md                 - Complete tool documentation
```

### **Documentation**
```
✅ agentic/design/architecture.md  - Architecture
✅ agentic/tools/README.md         - Complete tool docs
✅ utils.py                        - Helper functions
✅ data/external/                  - 14 knowledge articles
```

### **Database Setup**
```
✅ 01_external_db_setup.ipynb  - Creates CultPass DB
✅ 02_core_db_setup.ipynb      - Creates UdaHub DB + loads articles
✅ data/models/cultpass.py     - CultPass database schema
✅ data/models/udahub.py       - UdaHub database schema
```

---

## ⏳ What You Need to Build

### **1. Agents** (4 agents - Priority: HIGH)
Location: `agentic/agents/`

Create these files:
```python
# agentic/agents/__init__.py
from agentic.agents.classifier_agent import create_classifier_agent
from agentic.agents.knowledge_agent import create_knowledge_agent  
from agentic.agents.account_agent import create_account_agent
from agentic.agents.escalation_agent import create_escalation_agent

__all__ = [
    'create_classifier_agent',
    'create_knowledge_agent',
    'create_account_agent',
    'create_escalation_agent'
]
```

**Required agent files:**
- [ ] `classifier_agent.py` - Categorizes tickets (no tools)
- [ ] `knowledge_agent.py` - Uses KNOWLEDGE_TOOLS
- [ ] `account_agent.py` - Uses ACCOUNT_TOOLS
- [ ] `escalation_agent.py` - Uses create_escalation_ticket

### **2. Workflow** (1 file - Priority: HIGH)
Location: `agentic/workflow.py`

Replace current sample code with supervisor that orchestrates your 4 agents.

**Key imports you'll need:**
```python
from langchain_openai import ChatOpenAI
from langgraph_supervisor import create_supervisor
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage

from agentic.agents import (
    create_classifier_agent,
    create_knowledge_agent,
    create_account_agent,
    create_escalation_agent
)
```

### **3. Testing** (1 file - Priority: MEDIUM)
Location: `03_agentic_app.ipynb`

Update with:
- Import your orchestrator
- Create test cases
- Demo scenarios
- Memory persistence tests

### **4. Logging** (Optional - Priority: LOW)
Location: `agentic/logging_config.py`

Add structured logging for:
- Ticket received
- Classification results
- Agent calls
- Tool usage
- Final resolution

---

## 🚀 Quick Start Steps

### **Step 1: Set Up Databases** (15 min)
```bash
# Run these notebooks in Jupyter
1. Open 01_external_db_setup.ipynb
2. Run all cells
3. Open 02_core_db_setup.ipynb
4. Run all cells

# Verify databases created:
# - data/external/cultpass.db
# - data/core/udahub.db
```

### **Step 2: Test Your Tools** (5 min)
```python
# In a Python console or notebook:
from agentic.tools import ALL_TOOLS
from agentic.state import create_initial_state
from agentic.memory_manager import get_memory_manager

print(f"Tools available: {len(ALL_TOOLS)}")
# Should show: 13

state = create_initial_state("TEST-001", "test_user", "Test message")
print(f"State created: {state['ticket_id']}")
# Should show: TEST-001

memory = get_memory_manager()
print("Memory manager ready!")
```

### **Step 3: Implement First Agent** (60 min)
Create `agentic/agents/classifier_agent.py`:

```python
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent

def create_classifier_agent(llm: ChatOpenAI):
    """Classifies tickets by category and urgency"""
    system_prompt = SystemMessage(content="""
    You are a ticket classifier.
    
    Analyze the ticket and return JSON with:
    - category: technical/billing/account/reservation/general
    - urgency: low/medium/high/critical
    - keywords: list of relevant keywords
    - recommended_agent: knowledge/account_ops/escalation
    
    Rules:
    - "blocked" or "refund" → critical urgency, escalation
    - "how to" questions → knowledge agent
    - Account queries → account_ops agent
    """)
    
    return create_react_agent(
        name="classifier",
        model=llm,
        prompt=system_prompt,
        tools=[]  # No tools - pure classification
    )
```

### **Step 4: Implement Remaining Agents** (2-3 hours)
Follow same pattern for:
- `knowledge_agent.py` (with KNOWLEDGE_TOOLS)
- `account_agent.py` (with ACCOUNT_TOOLS)
- `escalation_agent.py` (with create_escalation_ticket)

### **Step 5: Build Workflow** (1-2 hours)
Update `agentic/workflow.py` to orchestrate all agents.

### **Step 6: Test End-to-End** (1-2 hours)
Update `03_agentic_app.ipynb` with test cases.

---

## 📊 Project Status

| Component | Status | Files |
|-----------|--------|-------|
| **Data Setup** | ✅ Complete | DB notebooks, 14 articles |
| **Tools** | ✅ Complete | 13 tools in `tools/` |
| **State** | ✅ Complete | `state.py` |
| **Memory** | ✅ Complete | `memory_manager.py` |
| **Architecture** | ✅ Draft | `design/architecture.md` |
| **Agents** | ⏳ Todo | Need 4 agent files |
| **Workflow** | ⏳ Todo | Update `workflow.py` |
| **Testing** | ⏳ Todo | Update notebook |
| **Logging** | ⏳ Optional | New file needed |

**Overall: ~45% Complete**

---

## 📚 Key Reference Files

| File | Purpose |
|------|---------|
| `agentic/state.py` | State structure with all fields |
| `agentic/memory_manager.py` | Memory functions |
| `agentic/tools/README.md` | Complete tool documentation |
| `agentic/design/architecture.md` | Your architecture design |

---

## 💡 Implementation Tips

### **For Each Agent:**
1. Define system prompt clearly
2. Assign appropriate tools
3. Test independently before integration
4. Document expected inputs/outputs

### **Agent Node Pattern:**
```python
def agent_node(state: SupportTicketState, llm: ChatOpenAI) -> SupportTicketState:
    """Node function that manages state"""
    # 1. Read from state
    # 2. Optional: Add memory context
    # 3. Call agent
    # 4. Update state
    return updated_state
```

### **Workflow Pattern:**
```python
# Create all agents
llm = ChatOpenAI(model="gpt-4o-mini")
agent1 = create_agent1(llm)
agent2 = create_agent2(llm)

# Create supervisor
orchestrator = create_supervisor(
    model=llm,
    agents=[agent1, agent2, ...],
    prompt=supervisor_prompt,
    add_handoff_back_messages=True,
    output_mode="last_message"
).compile(checkpointer=MemorySaver())
```

---

## ⏱️ Estimated Time Remaining

- **Agents**: 3-4 hours (all 4 agents)
- **Workflow**: 1-2 hours  
- **Testing**: 2-3 hours
- **Logging**: 1-2 hours (optional)
- **Documentation**: 1 hour

**Total: 8-12 hours**

---

## 🎯 Success Criteria (Rubric)

- [x] Database setup complete
- [x] 14 knowledge articles  
- [x] 13 tools implemented
- [x] State management
- [x] Memory system
- [ ] Architecture document (update as needed)
- [ ] 4+ agents implemented
- [ ] Workflow orchestration
- [ ] Routing logic
- [ ] Memory integration demonstrated
- [ ] End-to-end testing
- [ ] Logging implemented

---

## 🆘 If You Get Stuck

**Import errors?**
- Make sure you're in the `starter/` directory
- Check that `__init__.py` files exist in package folders

**Can't see tools?**
```python
from agentic.tools import ALL_TOOLS
print([tool.name for tool in ALL_TOOLS])
```

**State/Memory not working?**
```python
from agentic.state import create_initial_state
from agentic.memory_manager import get_memory_manager

# Test state
state = create_initial_state("T1", "U1", "Test")
print(state.keys())

# Test memory
memory = get_memory_manager()
config = memory.get_session_config("T1")
print(config)
```

---

## 🎉 You're Ready!

Everything is set up. Focus on:
1. **Implementing the 4 agents** (most important)
2. **Connecting them in workflow.py**
3. **Testing everything together**

**Start with the classifier agent and build from there!** 🚀

