package main

import (
	"flag"
	"fmt"
	"image"
	"image/color"
	"image/png"
	"log"
	"os"
)

//I added a mechanism to make customizing image output a lot easier, see
//the use of WriteDebugImage in MyBot.go
//I'll leave this here for reference, since it works also
/*if *imageOutPrefix != "" {
    fname := fmt.Sprintf("%s.%d.png", *imageOutPrefix, s.Turn)
    //fmt.Printf("making image: %s\n", fname)
    f, err := os.Open(fname, os.O_WRONLY | os.O_CREATE, 0666)
    if err != nil {
        log.Panicf("Couldn't open %s (%s)", fname, err)
    }
    defer f.Close()
    err = png.Encode(f, s.Map)
    if err != nil {
        log.Panicf("Couldn't encode png (%s)", err)
    }
}*/

type ImageHelper struct {
	m     *Map
	pixel func(row, col int) color.NRGBA
}

func (ih ImageHelper) ColorModel() color.Model {
	return color.NRGBAModel
}
func (ih ImageHelper) Bounds() image.Rectangle {
	return image.Rect(0, 0, ih.m.Cols*4, ih.m.Rows*4)
}
func (ih ImageHelper) At(x, y int) color.Color {
	return ih.pixel(y/4, x/4)
}
func (s *State) WriteDebugImage(Desc string, At func(row, col int) color.NRGBA) {

	//use -imgprefix="bot0" to make a series of images (bot0.0.png ... bot0.N.png) which
	//illustrate the bot's knowledge of the map at each turn. If you want the images in a
	//subdirectory, make sure you create the directory first. (e.g., -imgprefix="images/bot0")
	imageOutPrefix := flag.String("imgprefix", "", "prefix for helpful debugging images")

	if imageOutPrefix == nil {
		return
	}

	fname := fmt.Sprintf("%s.%s.%3.3d.png", *imageOutPrefix, Desc, s.Turn)
	//fmt.Printf("making image: %s\n", fname)
	f, err := os.OpenFile(fname, os.O_WRONLY|os.O_CREATE, 0666)
	if err != nil {
		log.Panicf("Couldn't open %s (%s)", fname, err)
	}
	defer f.Close()
	err = png.Encode(f, ImageHelper{s.Map, At})
	if err != nil {
		log.Panicf("Couldn't encode png (%s)", err)
	}
}

func (o Item) Color() color.NRGBA {
	switch o {
	case UNKNOWN:
		return color.NRGBA{0xb0, 0xb0, 0xb0, 0xff}
	case WATER:
		return color.NRGBA{0x10, 0x10, 0x50, 0xff}
	case FOOD:
		return color.NRGBA{0xe0, 0xe0, 0xc0, 0xff}
	case LAND:
		return color.NRGBA{0x8b, 0x45, 0x13, 0xff}
	case DEAD:
		return color.NRGBA{0x69, 0x33, 0x05, 0xff}
	case MY_ANT:
		return color.NRGBA{0xf0, 0x00, 0x00, 0xff}
	case ANT_1:
		return color.NRGBA{0xf0, 0xf0, 0x00, 0xff}
	case ANT_2:
		return color.NRGBA{0x00, 0xf0, 0x00, 0xff}
	case ANT_3:
		return color.NRGBA{0x00, 0x00, 0xf0, 0xff}
	case ANT_4:
		return color.NRGBA{0xf0, 0x00, 0xf0, 0xff}
	case ANT_5:
		return color.NRGBA{0xf0, 0xf0, 0xf0, 0xff}
	case ANT_6:
		return color.NRGBA{0x80, 0x80, 0x00, 0xff}
	case ANT_7:
		return color.NRGBA{0x00, 0x80, 0x80, 0xff}
	case ANT_8:
		return color.NRGBA{0x80, 0x00, 0x80, 0xff}
	case ANT_9:
		return color.NRGBA{0x80, 0x00, 0xf0, 0xff}
	}
	return color.NRGBA{0x00, 0x00, 0x00, 0xff}
}

//implement Image for fancy image debugging
func (m *Map) ColorModel() color.Model {
	return color.NRGBAModel
}
func (m *Map) Bounds() image.Rectangle {
	return image.Rect(0, 0, m.Cols*4, m.Rows*4)
}
func (m *Map) At(x, y int) color.Color {
	loc := m.FromRowCol(y/4, x/4)
	return m.itemGrid[loc].Color()
}
