package main

import (
	"log"
	"math"
	"strconv"
)

//Item represents all the various items that may be on the map
type Item int8

const (
	UNKNOWN Item = iota - 5
	WATER
	FOOD
	LAND
	DEAD
	MY_ANT //= 0
	ANT_1
	ANT_2
	ANT_3
	ANT_4
	ANT_5
	ANT_6
	ANT_7
	ANT_8
	ANT_9

	MY_HILL //= 10
	HILL_1
	HILL_2
	HILL_3
	HILL_4
	HILL_5
	HILL_6
	HILL_7
	HILL_8
	HILL_9

	MY_OCCUPIED_HILL //= 20
	OCCUPIED_HILL_1
	OCCUPIED_HILL_2
	OCCUPIED_HILL_3
	OCCUPIED_HILL_4
	OCCUPIED_HILL_5
	OCCUPIED_HILL_6
	OCCUPIED_HILL_7
	OCCUPIED_HILL_8
	OCCUPIED_HILL_9
)

//IsOccupied returns true if hillOrAnt is an occupied ant hill.
func (hillOrAnt Item) IsOccupied() bool {
	if hillOrAnt >= MY_OCCUPIED_HILL && hillOrAnt <= OCCUPIED_HILL_9 {
		return true
	}
	return false
}

//IsAnt returns true if o is an ant or occupied hill
func (o Item) IsAnt() bool {
	if o >= MY_OCCUPIED_HILL && o <= OCCUPIED_HILL_9 {
		return true
	}
	if o >= MY_ANT && o <= ANT_9 {
		return true
	}
	return false
}

//IsHill returns true if o is an un/occupied hill
func (o Item) IsHill() bool {
	if o >= MY_OCCUPIED_HILL && o <= OCCUPIED_HILL_9 {
		return true
	}
	if o >= MY_HILL && o <= HILL_9 {
		return true
	}
	return false
}

//Player returns the player number of the given ant/hill (0 - 9)
func (o Item) Player() int {
	if o < 0 || o > OCCUPIED_HILL_9 {
		log.Panicf("Expected an ant or a hill!")
	}
	return int(o) % 10
}

//ToUnoccupied returns the HILL_X version of the given hill or ant.
func (hillOrAnt Item) ToUnoccupied() Item {
	return Item(hillOrAnt.Player()) + MY_HILL
}

//ToOccupied returns the OCCUPIED_HILL_X version of the given hill or ant.
func (hillOrAnt Item) ToOccupied() Item {
	return Item(hillOrAnt.Player()) + MY_OCCUPIED_HILL
}

//ToAnt returns the ANT_X version of the given hill or ant.
func (hillOrAnt Item) ToAnt() Item {
	return Item(hillOrAnt.Player())
}

//Symbol returns the symbol for the ascii diagram
func (o Item) Symbol() byte {
	switch o {
	case UNKNOWN:
		return '.'
	case WATER:
		return '%'
	case FOOD:
		return '*'
	case LAND:
		return ' '
	case DEAD:
		return '!'
	}
	if o >= MY_HILL && o <= HILL_9 {
		return byte(o-MY_HILL) + '0'
	}
	if o >= MY_OCCUPIED_HILL && o <= OCCUPIED_HILL_9 {
		return byte(o-MY_OCCUPIED_HILL) + 'A'
	}
	if o < MY_ANT || o > ANT_9 {
		log.Panicf("invalid item: %v", o)
	}
	return byte(o) + 'a'
}

//FromSymbol reverses Symbol
func FromSymbol(ch byte) Item {
	switch ch {
	case '.':
		return UNKNOWN
	case '%':
		return WATER
	case '*':
		return FOOD
	case ' ':
		return LAND
	case '!':
		return DEAD
	}
	if ch >= '0' && ch <= '9' {
		return MY_HILL + Item(ch-'0')
	}
	if ch >= 'A' && ch <= 'J' {
		return MY_OCCUPIED_HILL + Item(ch-'A')
	}
	if ch < 'a' || ch > 'j' {
		log.Panicf("invalid item symbol: %v", ch)
	}
	return Item(ch) + 'a'
}

//Location combines (Row, Col) coordinate pairs for use as keys in maps (and in a 1d array)
type Location int

type Map struct {
	Rows int
	Cols int

	itemGrid []Item

	Ants         map[Location]Item
	Hills        map[Location]Item
	Dead         map[Location]Item
	Water        map[Location]bool
	Food         map[Location]bool
	Destinations map[Location]bool
	Frontier     map[Location]bool
	MagnetVal    map[Location]float64
	ExploreVal   map[Location]float64
	FoodVal      map[Location]float64
	EnemyVal     map[Location]float64
	StepDirMap   map[Location]map[Location]StepDir

	//DirMap       map[Location]map[Location]Direction
	//StepMap      map[Location]map[Location]Int
}

//Newmap returns a newly constructed blank map.
func NewMap(Rows, Cols int) *Map {
	var loc = Location(-1)
	var sd = StepDir{Steps: -1, Dir: NoMovement}
	var sdm = make(map[Location]map[Location]StepDir)
	for i := range sdm {
		sdm[i] = map[Location]StepDir{loc: sd}
	}
	m := &Map{
		Rows:       Rows,
		Cols:       Cols,
		Water:      make(map[Location]bool),
		itemGrid:   make([]Item, Rows*Cols),
		StepDirMap: make(map[Location]map[Location]StepDir),
		//StepDirMap: sdm,
	}

	m.Reset()
	return m
}

//mapStruct for initializing nested maps
type SDMap struct {
	m map[Location]StepDir
}

//String returns an ascii diagram of the map.
func (m *Map) String() string {
	str := ""
	for row := 0; row < m.Rows; row++ {
		for col := 0; col < m.Cols; col++ {
			s := m.itemGrid[row*m.Cols+col].Symbol()
			str += string([]byte{s}) + " "
		}
		str += "\n"
	}
	return str
}

//StringDir returns an ascii diagram of the StepDir map's directions
func (m *Map) StringDir(loc Location) string {
	//first construct a 2d array of the map
	str := ""
	var dir_map [][]string
	for key, value := range m.StepDirMap[loc] {
		row, col := m.FromLocation(key)
		dir_map[row][col] = value.Dir.String()

	}
	for r := range dir_map {
		for c := range dir_map[r] {
			str += dir_map[r][c] + " "
		}
		str += "\n"
	}
	return str
}

//StringStep returns an ascii diagram of the StepDir map's step counts
func (m *Map) StringStep(loc Location) string {
	str := ""
	dir_map := make([][]string, m.Rows)
	for i := range dir_map {
		dir_map[i] = make([]string, m.Cols)
	}

	for key, value := range m.StepDirMap[loc] {
		log.Print("key: value: ", key, value)
		row, col := m.FromLocation(key)
		log.Print("row col: ", row, col)
		log.Print(strconv.Itoa(value.Steps))
		dir_map[row][col] = strconv.Itoa(value.Steps)
	}
	for r := range dir_map {
		for c := range dir_map[r] {
			str += dir_map[r][c] + " "
		}
		str += "\n"
	}
	return str
}

//Reset clears the map (except for water) for the next turn
func (m *Map) Reset() {
	for i := range m.itemGrid {
		m.itemGrid[i] = UNKNOWN
	}
	for i, val := range m.Water {
		if val {
			m.itemGrid[i] = WATER
		}
	}
	m.Ants = make(map[Location]Item)
	m.Hills = make(map[Location]Item)
	m.Dead = make(map[Location]Item)
	m.Food = make(map[Location]bool)
	m.Destinations = make(map[Location]bool)
}

//Item returns the item at a given location
func (m *Map) Item(loc Location) Item {
	return m.itemGrid[loc]
}

//AddWater adds water to the map.
func (m *Map) AddWater(loc Location) {
	m.Water[loc] = true
	m.itemGrid[loc] = WATER
}

//AddAnt adds an ant to the map. It can also accept an occupied ant hill.
func (m *Map) AddAnt(loc Location, ant Item) {
	m.Ants[loc] = ant.ToAnt()
	if ant.IsOccupied() {
		m.Hills[loc] = ant.ToUnoccupied()
	}
	if m.Hills[loc] == ant.ToUnoccupied() {
		ant = ant.ToOccupied() //be sure to record the right thing in the itemGrid
	}
	m.itemGrid[loc] = ant
}

//AddHill takes an unoccupied ant hill and adds it to the map.
func (m *Map) AddHill(loc Location, hill Item) {
	m.Hills[loc] = hill.ToUnoccupied()
	if m.Ants[loc] == hill.ToAnt() {
		hill = hill.ToOccupied() //an ant has already been added here!
	}
	m.itemGrid[loc] = hill
}

//AddLand adds a circle of land centered on the given location
func (m *Map) AddLand(center Location, viewrad2 int) {
	m.DoInRad(center, viewrad2, func(row, col int) {
		loc := m.FromRowCol(row, col)
		if m.itemGrid[loc] == UNKNOWN {
			m.itemGrid[loc] = LAND
		}
	})
}

//DoInRad performs the given action for every square within the given circle.
func (m *Map) DoInRad(center Location, rad2 int, Action func(row, col int)) {
	row1, col1 := m.FromLocation(center)
	for row := row1 - m.Rows/2; row < row1+m.Rows/2; row++ {
		for col := col1 - m.Cols/2; col < col1+m.Cols/2; col++ {
			row_delta := row - row1
			col_delta := col - col1
			if row_delta*row_delta+col_delta*col_delta < rad2 {
				Action(row, col)
			}
		}
	}
}

//DoInRadRet performs the given action for every square within the given circle with added return in
func (m *Map) DoInRadRet(center Location, rad2 int, Action func(row, col int) int) {
	var ret int
	row1, col1 := m.FromLocation(center)
	for row := row1 - m.Rows/2; row < row1+m.Rows/2; row++ {
		for col := col1 - m.Cols/2; col < col1+m.Cols/2; col++ {
			row_delta := row - row1
			col_delta := col - col1
			if row_delta*row_delta+col_delta*col_delta < rad2 {
				ret += Action(row, col)
			}
		}
	}
	return ret
}

func (m *Map) AddDeadAnt(loc Location, ant Item) {
	m.Dead[loc] = ant
	m.itemGrid[loc] = DEAD
}

func (m *Map) AddFood(loc Location) {
	m.Food[loc] = true
	m.itemGrid[loc] = FOOD
}

func (m *Map) AddDestination(loc Location) {
	if m.Destinations[loc] {
		log.Panicf("Already have something at that destination!")
	}
	m.Destinations[loc] = true
}

func (m *Map) RemoveDestination(loc Location) {
	m.Destinations[loc] = false
}

//SafeDestination will tell you if the given location is a
//safe place to dispatch an ant. It considers water and both
//ants that have already sent an order and those that have not.
func (m *Map) SafeDestination(loc Location) bool {
	if _, exists := m.Water[loc]; exists {
		return false
	}
	if occupied := m.Destinations[loc]; occupied {
		return false
	}
	return true
}

//FromRowCol returns a Location given an (Row, Col) pair
func (m *Map) FromRowCol(Row, Col int) Location {
	for Row < 0 {
		Row += m.Rows
	}
	for Row >= m.Rows {
		Row -= m.Rows
	}
	for Col < 0 {
		Col += m.Cols
	}
	for Col >= m.Cols {
		Col -= m.Cols
	}

	return Location(Row*m.Cols + Col)
}

//FromLocation returns an (Row, Col) pair given a Location
func (m *Map) FromLocation(loc Location) (Row, Col int) {
	Row = int(loc) / m.Cols
	Col = int(loc) % m.Cols
	return
}

//Direction represents the direction concept for issuing orders.
type Direction int

const (
	North Direction = iota
	East
	South
	West

	NoMovement
)

func (d Direction) String() string {
	switch d {
	case North:
		return "n"
	case South:
		return "s"
	case West:
		return "w"
	case East:
		return "e"
	case NoMovement:
		return "-"
	}
	log.Panicf("%v is not a valid direction", d)
	return ""
}

func (d Direction) Opposite() Direction {
	switch d {
	case North:
		return South
	case South:
		return North
	case West:
		return East
	case East:
		return West
	case NoMovement:
		return NoMovement
	}
	log.Panicf("%v is not a valid direction", d)
	return NoMovement
}

// Location-Direction tuple struct. This is useful for a
// couple of functions
type LocDir struct {
	Loc Location
	Dir Direction
}

/*
 This is simply a tuple struct containing Steps, where Steps is a
 number of steps from a location and Dir, where Dir is a Direction that
 should be taken in order to get to the location
 This struct is used in the context StepDirMap.
 map[currentLoc] -> map[otherLocation] -> StepDir
 StepDir.Steps => # of steps from currentLoc to otherLocation
 StepDir.Direction => Dir to take from currentLoc to get to otherLoc
*/
type StepDir struct {
	Steps int
	Dir   Direction
}

//Allows for easy splitting of the LocDir struct
//Usage: given a slice s := []LocDir, for l, d := range s.Split()
func (ld *LocDir) Split() (Location, Direction) {
	return ld.Loc, ld.Dir
}

//Move returns a new location which is one step in the specified direction from the specified location.
func (m *Map) Move(loc Location, d Direction) Location {
	Row, Col := m.FromLocation(loc)
	switch d {
	case North:
		Row -= 1
	case South:
		Row += 1
	case West:
		Col -= 1
	case East:
		Col += 1
	case NoMovement: //do nothing
	default:
		log.Panicf("%v is not a valid direction", d)
	}
	return m.FromRowCol(Row, Col) //this will handle wrapping out-of-bounds numbers
}

//Return a slice of child Locations given a location and the direction taken to get to that location
// Note that the child array is ordered by direction
// so the index can be used as the direction
func (m *Map) Children(loc Location, d Direction) [4]LocDir {
	var child [4]LocDir
	var ld LocDir
	for i := 0; i < 5; i++ {
		if i != int(d) {
			ld.Loc = m.Move(loc, Direction(i))
			ld.Dir = Direction(i)
			child[i] = ld
		}
	}
	return child
}

//Return a slice of adjacent LocDir's given a location
//TODO, determine whether it's useful to return the direction taken as
//well, yes. It is.
// Or should I use multiple return values?
func (m *Map) Adjacent(loc Location) [4]LocDir {
	var child [4]LocDir
	var ld LocDir
	for i := 0; i < 4; i++ {
		ld.Loc = m.Move(loc, Direction(i))
		ld.Dir = Direction(i)
		child[i] = ld
	}
	return child
}

/** Given a location, give the first closest step to get to any
 square a set step distance from any point
 I'll also use this function to update the stepDistance
 map for each tile
**/
func (m *Map) PathMap(loc Location) { return }

//Define frontier. set m.Frontier[true]
func (m *Map) isFrontier(loc Location) {
	return
}

//Using row and col, compute manhattan Distance
func (m *Map) NaiveManhattanD(start Location, dest Location) int {
	start_row, start_col := m.FromLocation(start)
	dest_row, dest_col := m.FromLocation(dest)

	start_row64 := float64(start_row)
	start_col64 := float64(start_col)
	dest_row64 := float64(dest_row)
	dest_col64 := float64(dest_col)
	return int(math.Abs(start_row64-dest_row64) + math.Abs(start_col64-dest_col64))
}

//Use the table of stored distances to calculate the actual step
//between any two points, in the case that a location doesn't have
//any local step distances, return -1
//func (m *Map) StepDistance(start Location, dest Location) int { return }
