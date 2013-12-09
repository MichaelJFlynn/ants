// Util.go - helper class
package main

import (
	"container/heap"
	"container/list"
	"log"
	"strconv"
	//"math/rand"
)

var _ = strconv.Itoa(1)

/////////////////////
// Data Structures //
/////////////////////

//LIFO Stack built on top of the list structure
//To initialize :: stack := new(Stack)
//TODO - implement errror handling for illegal operations
type Stack struct {
	data list.List
}

//Returns size of stack
func (q *Stack) Len() int { return q.data.Len() }

//Push an item to the front of the stack
//Returns a reference to the Element container
func (q *Stack) Push(v interface{}) *list.Element {
	return q.data.PushFront(v)
}

//Peek - returns the last pushed element without popping it
func (q *Stack) Peek() interface{} {
	return q.data.Front().Value
}

//Pop - remove and return the last pushed element in the list
func (q *Stack) Pop() interface{} {
	return q.data.Remove(q.data.Front())
}

//General Queue type, implemented on top of list
//To initialize :: queue := new(Queue)
type Queue struct {
	data list.List
}

//Return size of the queue
func (q *Queue) Len() int { return q.data.Len() }

//Push item onto queue, and return reference to item just pushed
func (q *Queue) Push(v interface{}) *list.Element {
	return q.data.PushBack(v)
}

//Return reference to next item to be popped without popping
func (q *Queue) Peek() interface{} {
	return q.data.Front().Value
}

func (q *Queue) Pop() interface{} {
	return q.data.Remove(q.data.Front())
}

//Item - container for PriorityQueue
//Implementation taken from godoc
type QItem struct {
	//value    interface{}
	value    string
	priority int
	index    int
}

//General type PriorityQueue implemented on top of Go's heap
//To initialize :: pqueue := new(PQueue)
//Based on the example from the heap pkg page
//http://golang.org/pkg/container/heap/#pkg-examples
type PriorityQueue []*QItem

func (pq PriorityQueue) Len() int { return len(pq) }

//Comparison function for the priority queue
//This implementation means Pop gives the highest priority
func (pq PriorityQueue) Less(i, j int) bool {
	return pq[i].priority > pq[j].priority
}

//Given two indeces, swaps the values
func (pq PriorityQueue) Swap(i, j int) {
	pq[i], pq[j] = pq[j], pq[i]
	pq[i].index = i
	pq[j].index = j
}

func (pq *PriorityQueue) Push(v interface{}) {
	n := len(*pq)
	item := v.(*QItem)
	item.index = n
	*pq = append(*pq, item)
}

func (pq *PriorityQueue) Pop() interface{} {
	old := *pq
	n := len(old)
	item := old[n-1]
	item.index = -1 // for safety
	*pq = old[0 : n-1]
	return item
}

// update modifies the priority and value of an QItem in the queue.
func (pq *PriorityQueue) update(item *QItem, value string, priority int) {
	heap.Remove(pq, item.index)
	item.value = value
	item.priority = priority
	heap.Push(pq, item)
}

////////////////
//Algorithms //
////////////////

/*
 General Search BFS, given start location and target item type
 return a LocDir where the location is the item and the direction
 is the last direction taken to get to the item from the start
  So if searching from food to an ant, remember to take the reverse
 of the direction
*/
func (m *Map) Bfs(loc Location, obj Item) LocDir {
	isGoal := func(curLoc Location) bool {
		if m.Item(curLoc) == obj {
			return true
		}
		return false
	}
	//ret acts as the default return when either nothing is found
	//or the goal state is the cell.
	ret := LocDir{loc, NoMovement}
	ret.Loc = -1
	ret.Dir = NoMovement

	var depth int
	frontier := new(Queue) // make this Queue a type of LocDir
	var inFrontier = make(map[Location]bool)
	var explored = make(map[Location]bool) // the keys are only locations

	if isGoal(loc) {
		return ret
	}

	frontier.Push(ret)     // frontier is queue of LocDir
	inFrontier[loc] = true // keys to inFrontier are simply locations
	// I'm not sure whether I should set the keys to frontier to be a LocDir
	// as well.

	for {
		if frontier.Len() == 0 || depth > 10 {
			return ret
		}

		curLoc := frontier.Pop().(LocDir)
		inFrontier[curLoc.Loc] = false
		explored[curLoc.Loc] = true

		// Loop over adjacent Locations, action is a LocDir structure
		for _, action := range m.Adjacent(curLoc.Loc) {
			//if child not in explored or frontier
			if !explored[action.Loc] || !inFrontier[action.Loc] {
				if isGoal(action.Loc) {
					return action
				}
				frontier.Push(action)
				inFrontier[action.Loc] = true
			}
		}
		depth++
	}
	return ret
}

//UpdateFunction type
type uFunc func(loc Location, steps int, m *Map)

//increment a food value based on distance from nearest food
func updateFood(loc Location, steps int, m *Map) {
	m.FoodVal[loc] += 1.0 / float64(steps)
	return
}

//increment a to explore value based on distance from nearest non-visible
//mark
func updateExplore(loc Location, steps int, m *Map) {
	m.ExploreVal[loc] += 1.0 / float64(steps)
	return
}

//set cell as frontier if proper number of steps from any any ant
func updateFrontier(loc Location, steps int, m *Map) {
	return
}

/* Update BFS, just like previous BFS but takes a func to
modify the map values accordingly.
*/
func (m *Map) BfsUpdate(loc Location, fn uFunc) LocDir {

	//ret acts as the default return when either nothing is found
	//or the goal state is the cell.
	ret := LocDir{loc, NoMovement}
	ret.Loc = -1
	ret.Dir = NoMovement

	var depth int
	frontier := new(Queue) // make this Queue a type of LocDir
	var inFrontier = make(map[Location]bool)
	var explored = make(map[Location]bool) // the keys are only locations

	frontier.Push(ret)     // frontier is queue of LocDir
	inFrontier[loc] = true // keys to inFrontier are simply locations
	// I'm not sure whether I should set the keys to frontier to be a LocDir
	// as well.

	for {
		// Depth should be the viewRadius, but I'm not sure how to get this at
		// runtime yet.
		if frontier.Len() == 0 || depth > 7 {
			return ret
		}

		curLoc := frontier.Pop().(LocDir)
		inFrontier[curLoc.Loc] = false
		explored[curLoc.Loc] = true

		fn(curLoc.Loc, depth, m) //update function call

		// Loop over adjacent Locations, action is a LocDir structure
		for _, action := range m.Adjacent(curLoc.Loc) {
			//if child not in explored or frontier
			if !explored[action.Loc] || !inFrontier[action.Loc] {
				frontier.Push(action)
				inFrontier[action.Loc] = true
			}
		}
		depth++
	}
	return ret
}

//func AStar(start *Location, dest *Location, s *State) { return }

//////////////////////////
//Map Update functions //
//////////////////////////

//Iterate over all visible food and update food values
func (m *Map) SetFood() {
	for loc, food := range s.Map.Food {
		m.BfsUpdate(loc, upDateFood)
	}
}

//This gives values to the squares where there are less
//teammate ants
func (m *Map) SetMagnetVal(loc Location) {
	incAnt := func(row, col int) int {
		if m.Item[m.FromRowCol(row, col)].IsAnt() {
			return 1
		}
		return 0
	}
	m.DoInRadRet(loc, 7, incAnt)

}

///////////////////////////
// Ant Control Functions //
///////////////////////////

///////////////
//Deprecated //
///////////////

/*
 DLE or DepthLimitedExplore
 Exploration DFS, it updates map datastructures and simply explores
 to a certain depth with no target. This BFS should not ever be
 called once the map has been completely explored.

 At the time of this comment, this funcion is responsible for updating
 the StepDirMap. See documentation for type StepDir for more
 detailed info.

This function is not being used at the time of turnin,
 I've run into lot's of type issues when initializing nested maps.
*/
func (m *Map) DLE(loc Location, limit int) {
	for _, action := range m.Adjacent(loc) {
		m.RDLE(loc, action.Loc, limit-1, action.Dir)
	}
	return
}

func (m *Map) RDLE(root Location, loc Location, limit int, dir Direction) {
	if limit == 0 {
		return
	}
	var sd StepDir
	for _, action := range m.Adjacent(loc) {
		sd.Steps = 5 - limit
		sd.Dir = dir

		//log.Printf(strconv.Itoa(limit))

		//log.Printf("first if check.")
		if _, ok := m.StepDirMap[root]; ok {
			//log.Printf("root check passed")
			if _, ok := m.StepDirMap[root][loc]; ok {
				log.Printf("root loc passed")
				m.StepDirMap[root][loc] = sd
				//log.Printf("loc ", strconv.Itoa(int(loc)))
			} else {
				//log.Printf("root loc failed but recovered")
				m.StepDirMap[root] = make(map[Location]StepDir)
				m.StepDirMap[root][loc] = sd
				if sd.Steps == 1 {
					//log.Printf("steps ", strconv.Itoa(sd.Steps))
					//log.Printf("loc ", strconv.Itoa(int(loc)))
				}

			}
		} else {
			//log.Printf("m.StepDirMap[root] = make(map[Location]StepDir)")
			m.StepDirMap[root] = make(map[Location]StepDir)
			//log.Printf("did not panic")
		}
		//log.Printf("failed first if.")

		m.RDLE(root, action.Loc, limit-1, dir)
	}
}
