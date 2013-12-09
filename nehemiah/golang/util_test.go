package main

import (
	"testing"
)

func TestStack(t *testing.T) {
	stack := new(Stack)

	stack.Push("Last")
	stack.Push("in")
	stack.Push("first")
	stack.Push("out.")

	if stack.Peek() != "out." {
		t.Errorf("Peek method incorrect.")
	}
	if stack.Pop() != "out." {
		t.Errorf("Pop method incorrect.")
	}

}

func TestQueue(t *testing.T) {
	str_q := new(Queue)

	str_q.Push("First")
	str_q.Push("in")
	str_q.Push("first")
	str_q.Push("out.")

	if str_q.Pop() != "First" {
		t.Errorf("Ordering wrong.")
	}
	if str_q.Pop() != "in" {
		t.Errorf("Ordering wrong.")
	}
	if str_q.Pop() != "first" {
		t.Errorf("Ordering wrong.")
	}
	if str_q.Pop() != "out." {
		t.Errorf("Ordering wrong.")
	}

}

func TestPriorityQueue(t *testing.T) { return }

//TODO define
func TestBFS(t *testing.T) {
	m := NewMap(5, 5)
	m.Reset()

	//calling BFS on this map should return nil

}

func BenchmarkTestBFS(t *testing.B) { return }

func TestAstar(t *testing.T) { return }

func BenchmarkAstar(t *testing.B) { return }
