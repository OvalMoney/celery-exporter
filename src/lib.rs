use lru::LruCache;
use std::collections::HashMap;
use std::fmt;

use pyo3::prelude::*;
use pyo3::types::PyDict;

static CELERY_MISSING_DATA: &'static str = "undefined";

type CollectOutcome = (Option<String>, Option<String>, Option<f64>, Option<String>); // name, state, runtime, queue
type LatencyOutcome = (Option<String>, Option<String>, Option<f64>);

#[derive(Clone)]
struct Task {
    uuid: String,
    name: String,
    local_received: f64,
    runtime: Option<f64>,
    state: TaskState,
}

impl Default for Task {
    fn default() -> Self {
        Self {
            uuid: CELERY_MISSING_DATA.to_string(),
            name: CELERY_MISSING_DATA.to_string(),
            local_received: 0.0,
            runtime: None,
            state: TaskState::UNDEFINED,
        }
    }
}

impl Task {
    fn update_from_event(&mut self, evt: &PyDict) -> PyResult<()> {
        let kind: String = evt
            .get_item("type")
            .expect("Invalid Event: missing type")
            .extract()?; // GUARANTEED
        let splitted = kind.split("-");
        let state = splitted.collect::<Vec<&str>>()[1];
        let uuid = evt.get_item("uuid");
        let name = evt.get_item("name");

        if kind.contains("task") {
            if let Some(u) = uuid {
                self.uuid = u.to_string();
            }
            self.state = event_to_state(state);
            self.local_received = evt
                .get_item("local_received")
                .expect("Invalid Event: missing local_received")
                .extract()?;
            match name {
                Some(n) => self.name = n.extract()?,
                None => {}
            }
            if let Some(r) = evt.get_item("runtime") {
                self.runtime = Some(r.extract()?);
            }
        }
        Ok(())
    }
}

#[derive(Debug, Copy, Clone)]
enum TaskState {
    PENDING,
    RECEIVED,
    STARTED,
    FAILURE,
    RETRY,
    SUCCESS,
    REVOKED,
    REJECTED,
    UNDEFINED,
}
impl fmt::Display for TaskState {
    // UEUE Solution
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "{:?}", self)
    }
}

fn event_to_state(evt_kind: &str) -> TaskState {
    match evt_kind {
        "sent" => TaskState::PENDING,
        "received" => TaskState::RECEIVED,
        "started" => TaskState::STARTED,
        "failed" => TaskState::FAILURE,
        "retried" => TaskState::RETRY,
        "succeeded" => TaskState::SUCCESS,
        "revoked" => TaskState::REVOKED,
        "rejected" => TaskState::REJECTED,
        _ => TaskState::UNDEFINED,
    }
}

#[pyclass]
struct CeleryState {
    event_count: i32,
    task_count: i32,
    queue_by_task: HashMap<String, String>,
    tasks: LruCache<String, Task>,
}

#[pymethods]
impl CeleryState {
    #[new]
    fn new(obj: &PyRawObject, max_tasks_in_memory: usize) {
        obj.init(CeleryState {
            event_count: 0,
            task_count: 0,
            queue_by_task: HashMap::new(),
            tasks: LruCache::new(max_tasks_in_memory),
        });
    }

    fn collect(&mut self, evt: &PyDict) -> PyResult<CollectOutcome> {
        let mut task = Task::default();
        task.update_from_event(evt)?;

        match task.state {
            TaskState::SUCCESS | TaskState::FAILURE | TaskState::REVOKED => {
                let name: String = self.tasks.pop(&task.uuid).unwrap_or(task.clone()).name;
                let queue: String = self
                    .queue_by_task
                    .get(&name)
                    .unwrap_or(&CELERY_MISSING_DATA.to_string())
                    .into();

                return Ok((
                    Some(name),
                    Some(task.state.to_string()),
                    task.runtime,
                    Some(queue),
                ));
            }
            _ => {
                self.event(&task);

                let task_mut = self.tasks.get_mut(&task.uuid).unwrap();
                task_mut.state = task.state;
                let name: String = task_mut.name.clone();
                match evt.get_item("queue") {
                    Some(q) => {
                        self.queue_by_task.insert(name.to_string(), q.extract()?);
                    }
                    None => {}
                }

                let queue: String = self
                    .queue_by_task
                    .get(&name)
                    .unwrap_or(&CELERY_MISSING_DATA.to_string())
                    .into();
                return Ok((Some(name), Some(task.state.to_string()), None, Some(queue)));
            }
        }
    }

    fn latency(&mut self, evt: &PyDict) -> PyResult<LatencyOutcome> {
        let mut task = Task::default();
        task.update_from_event(evt)?;
        match task.state {
            TaskState::STARTED => {
                let prev_evt = self.tasks.get(&task.uuid);
                match prev_evt {
                    Some(p) => match p.state {
                        TaskState::RECEIVED => {
                            let name: String = p.name.clone();
                            let queue: String = self
                                .queue_by_task
                                .get(&name)
                                .unwrap_or(&CELERY_MISSING_DATA.to_string())
                                .into();
                            let latency = task.local_received - p.local_received;

                            return Ok((Some(name), Some(queue), Some(latency)));
                        }
                        _ => {}
                    },
                    None => {}
                }
            }
            _ => {}
        }
        return Ok((None, None, None));
    }
}

impl CeleryState {
    fn event(&mut self, task: &Task) {
        self.event_count += 1;

        match self.tasks.get(&task.uuid) {
            None => self.tasks.put(task.uuid.to_string(), task.clone()),
            _ => {}
        }

        match task.state {
            TaskState::RECEIVED => self.task_count += 1,
            _ => {}
        }
    }
}

#[pymodule]
fn celery_state(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<CeleryState>()?;
    Ok(())
}
