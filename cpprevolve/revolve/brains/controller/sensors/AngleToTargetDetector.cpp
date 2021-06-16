//
// Created by matteo on 2/28/20.
//

#include "AngleToTargetDetector.h"
//#include <opencv2/imgproc/imgproc.hpp>
//#include <opencv2/highgui/highgui.hpp>
#include <iostream>
#include <cmath>

revolve::AngleToTargetDetector::AngleToTargetDetector(const unsigned int shrink_factor, const bool show_image)
    : Sensor(1)
    , show_image(show_image)
    , shrink_factor(shrink_factor)
//    , angle(std::atan(img.cols/img.rows) * 180 / M_PI)
    , angle(NAN)
{}

void revolve::AngleToTargetDetector::read(double *input)
{
    input[0] = detect_angle();
}

//float revolve::AngleToTargetDetector::detect_angle()
//{
//    get_image(raw_image);
//    unsigned int image_cols = raw_image.cols/shrink_factor;
//    unsigned int image_rows = raw_image.rows/shrink_factor;
//    cv::resize(raw_image, image, cv::Size(image_cols, image_rows));
//
//    cv::medianBlur(image, image_blur, 5);
//    cv::cvtColor(image_blur, image_hsv, cv::COLOR_BGR2HSV);
//
//    //green
//    const int gLowH1=35,gHighH1=40,gLowH2=41,gHighH2=59,gLowS1=140,gLowS2=69,gHighS=255,gLowV=104,gHighV=255;
//    //blue
//    const int bLowH=99,bHighH=121,bLowS=120,bHighS=255,bLowV=57,bHighV=211;
//
//    //detecting Blue
//    cv::inRange(image_hsv, cv::Scalar(bLowH,bLowS, bLowV), cv::Scalar(bHighH,bHighS, bHighV)   ,image_blue);
//    //detecting Green
//    cv::inRange(image_hsv, cv::Scalar(gLowH1,gLowS1, gLowV), cv::Scalar(gHighH1,gHighS, gHighV),image_green1);
//    cv::inRange(image_hsv, cv::Scalar(gLowH2,gLowS2, gLowV), cv::Scalar(gHighH2,gHighS, gHighV),image_green2);
//    cv::add(image_green1, image_green2, image_green);
//
//    std::vector<std::vector<cv::Point>> contours_blue, contours_green;; //contours_red, contours_yellow;
//
//    cv::findContours(image_blue, contours_blue, cv::RETR_EXTERNAL, cv::CHAIN_APPROX_NONE);
//    cv::findContours(image_green, contours_green, cv::RETR_EXTERNAL, cv::CHAIN_APPROX_NONE);
//    //cv::findContours(image_red, contours_red, cv::RETR_EXTERNAL, cv::CHAIN_APPROX_NONE);
//    //cv::findContours(image_yellow, contours_yellow, cv::RETR_EXTERNAL, cv::CHAIN_APPROX_NONE);
//
//    std::vector<cv::Rect> rect_coord, rect_coord_blue, rect_coord_green; //rect_coord_red, rect_coord_yellow;
//
//    // blue contours
//    for (const std::vector<cv::Point> &contours_blue_line : contours_blue) {
//        double image_blue_area_buf = cv::contourArea(contours_blue_line);
//
//        if (image_blue_area_buf > 5) {
//            cv::Rect bounding_rect = cv::boundingRect(contours_blue_line);
//            rect_coord_blue.emplace_back(bounding_rect);
//        }
//    }
//
//    // green contours
//    for (const std::vector<cv::Point> &contours_green_line : contours_green) {
//        double image_blue_area_buf = cv::contourArea(contours_green_line);
//
//        if (image_blue_area_buf > 5) {
//            cv::Rect bounding_rect = cv::boundingRect(contours_green_line);
//            rect_coord_green.emplace_back(bounding_rect);
//        }
//    }
//
//    //// red contours
//    //for (const std::vector<cv::Point> &contours_red_line : contours_red) {
//    //    double image_blue_area_buf = cv::contourArea(contours_red_line);
//    //
//    //    if (image_blue_area_buf > 5) {
//    //        cv::Rect bounding_rect = cv::boundingRect(contours_red_line);
//    //        rect_coord_red.emplace_back(bounding_rect);
//    //    }
//    //}
//    //
//    //// yellow contours
//    //for (const std::vector<cv::Point> &contours_yellow_line : contours_yellow) {
//    //    double image_blue_area_buf = cv::contourArea(contours_yellow_line);
//    //
//    //    if (image_blue_area_buf > 5) {
//    //        cv::Rect bounding_rect = cv::boundingRect(contours_yellow_line);
//    //        rect_coord_yellow.emplace_back(bounding_rect);
//    //    }
//    //}
//
//    rect_coord.reserve( rect_coord_blue.size() + rect_coord_green.size() ); // preallocate memory
//    // + rect_coord_red.size() + rect_coord_yellow.size()
//    rect_coord.insert( rect_coord.end(), rect_coord_blue.begin(), rect_coord_blue.end() );
//    rect_coord.insert( rect_coord.end(), rect_coord_green.begin(), rect_coord_green.end() );
//    //rect_coord.insert( rect_coord.end(), rect_coord_red.begin(), rect_coord_red.end() );
//    //rect_coord.insert( rect_coord.end(), rect_coord_yellow.begin(), rect_coord_yellow.end() );
//
//// ----- MAGIC GONGJIN CODE HERE ----------------------------------------------
//    unsigned int num = rect_coord.size();
//    int distanceBox[num][num], distanceBoxSum[num], numBox[num], minDistanceBox[num], min2DistanceBox[num],rectBoxHeight = 0, rectBoxHeightMax = 0;
//    for (int i = 0; i < num; i++) //calculating the suitable(medium) value of height
//    {
//        if (rect_coord[i].height > rectBoxHeightMax)
//        {
//            rectBoxHeight = rectBoxHeightMax; // set this value as the height of box
//            rectBoxHeightMax = rect_coord[i].height;
//        }
//        else if (rect_coord[i].height > rectBoxHeight)
//            rectBoxHeight = rect_coord[i].height;
//    }
//
//    for (int j = 0; j < num; j++) //calculating the value of minimum and the second minimum distance for each box
//    {
//        minDistanceBox[j] = 800;
//        min2DistanceBox[j] = 800;
//        for (int x = 0; x < num; x++)
//        {
//            if (j != x)
//            {
//                distanceBox[j][x] = std::min(
//                        std::abs(rect_coord[j].tl().x - rect_coord[x].br().x),
//                        std::abs(rect_coord[j].br().x - rect_coord[x].tl().x)
//                );
//
//                if (distanceBox[j][x] < minDistanceBox[j])
//                {
//                    min2DistanceBox[j] = minDistanceBox[j]; //the second minimum distance
//                    minDistanceBox[j] = distanceBox[j][x]; //the minimun distance
//                }
//                else if (distanceBox[j][x] < min2DistanceBox[j])
//                {
//                    min2DistanceBox[j] = distanceBox[j][x];
//                }
//            }
//        }
//        distanceBoxSum[j] = minDistanceBox[j] + min2DistanceBox[j];
//    }
//
//    for (int i =0; i < num; i++) //sequence from minimum distance to maximum distance
//    {
//        numBox[i] = 0;
//        for (int j=0; j < num; j++)
//        {
//            if (i != j) // get the Box[i] sequence
//            {
//                if (distanceBoxSum[i] > distanceBoxSum[j])
//                    numBox[i]+=1; //numBox[i] = numBox[i] +1, save the number
//                if (distanceBoxSum[i] == distanceBoxSum[j])
//                {
//                    if (minDistanceBox[i] >= minDistanceBox[j]) //always have the same distance between two points each other
//                        numBox[i]+=1; //
//                }
//            }
//        }
//    }
//    //-------------difine the ROIs of robot------------
//    int lastnum = num, robNum, minRectCoorX[num], minRectCoorY[num], maxRectCoorX[num], maxRectCoorY[num];
//    for (robNum = 0; lastnum >= 2 && robNum < num; robNum++)
//    {
//        int minNumBox=100;
//        for (int k = 0; k <num; k++) //get the minNumBox between the rest
//        {
//            minNumBox = std::min(numBox[k], minNumBox);
//        }
//        for (int i = 0; i < num; i++) //get the coordination of rectangle of robot from boxes
//        {
//            if (numBox[i] == minNumBox) //find the minimum one between the rest (usually it is 0 when 1 robot)
//            {
//                lastnum --;
//                if (num > 2) //when robot only have 2 boxes at least, just combine the two boxes
//                    numBox[i] = 100; //make it not included in the rest
//                minRectCoorX[robNum] = rect_coord[i].tl().x;
//                minRectCoorY[robNum] = rect_coord[i].tl().y;
//                maxRectCoorX[robNum] = rect_coord[i].br().x;
//                maxRectCoorY[robNum] = rect_coord[i].br().y;
//                int bufnum = 0, jBox[50] = {0};
//                for (int j = 0; j < num; j++) //calculating the coordination of rectangle incluing boxes belong to the distance area
//                {
//                    //-------------the first threshold condition-------------------
//                    if (j != i && numBox[j] != 100 && distanceBox[i][j] < 4.3 * rectBoxHeight) //3.4, 3.5, 4.5, 4.3 justify if the box belong to the same robot by distance of boxeswith the center box
//                    {
//                        jBox[bufnum] = j;
//                        lastnum --;
//                        bufnum ++; //the number of boxes that match the threshold of (distanceBox[i][j] < 3.4 * rectBoxHeight)
//                    }
//                    //----calculating the max distance between boxes after the first threshold condition, preparing for next--------
//                    if (j == num - 1 && bufnum >= 1) //bufnum >= 1 (it have two candidate at least)
//                    {
//                        int maxBoxDisOut[num], max_in_out[num][num],maxBoxDisOutNum[num];
//                        for (int buf = 0; buf < bufnum; buf++) //calculating the max distance between boxes in jBox[bufnum]
//                        {
//                            maxBoxDisOut[jBox[buf]] = 0;
//                            int rectCoor_tl_br, rectCoor_br_tl;
//                            if (bufnum == 1) // one other box and one center box
//                            {
//                                rectCoor_tl_br = std::abs(rect_coord[i].tl().x - rect_coord[jBox[0]].br().x); //calculating the inside or outside distance between the same boxes
//                                rectCoor_br_tl = std::abs(rect_coord[i].br().x - rect_coord[jBox[0]].tl().x); //calculating the inside or outside distance between the same boxes
//                                maxBoxDisOut[jBox[0]] = std::min(rectCoor_tl_br,rectCoor_br_tl); //max, min
//                            }
//                            else
//                            {
//                                for (int buff = 0; buff < bufnum; buff++)
//                                {
//                                    rectCoor_tl_br = std::abs(rect_coord[jBox[buf]].tl().x - rect_coord[jBox[buff]].br().x); //calculating the inside or outside distance between the same boxes
//                                    rectCoor_br_tl = std::abs(rect_coord[jBox[buf]].br().x - rect_coord[jBox[buff]].tl().x); //calculating the inside or outside distance between the same boxes
//                                    max_in_out[jBox[buf]][jBox[buff]] = std::min(rectCoor_tl_br,rectCoor_br_tl); //max,min
//                                    if (max_in_out[jBox[buf]][jBox[buff]] > maxBoxDisOut[jBox[buf]])
//                                    {
//                                        maxBoxDisOut[jBox[buf]] = max_in_out[jBox[buf]][jBox[buff]];
//                                        maxBoxDisOutNum[buf] = jBox[buff];
//                                    }
//                                }
//                            }
//                        }
//                        //bufnum >1 guarantte the robot have center box and two other box (bufnum=2) at least, or not go to compare center box and another one box
//                        if (bufnum >= 2)
//                        {
//                            int delNum = 0;
//                            for (int bufff = 0; bufff < bufnum; bufff++) //compare the max distance (robot size from left to right) of boxes in jBox[bufnum]
//                            {
//                                if (maxBoxDisOut[jBox[bufff]] < 6.2 * rectBoxHeight) //if > the length of robot, delete far one, get the near one as rectangle
//                                {
//                                    minRectCoorX[robNum] = std::min(rect_coord[jBox[bufff]].tl().x, minRectCoorX[robNum]);
//                                    minRectCoorY[robNum] = std::min(rect_coord[jBox[bufff]].tl().y, minRectCoorY[robNum]);
//                                    maxRectCoorX[robNum] = std::max(rect_coord[jBox[bufff]].br().x, maxRectCoorX[robNum]);
//                                    maxRectCoorY[robNum] = std::max(rect_coord[jBox[bufff]].br().y, maxRectCoorY[robNum]);
//                                    numBox[jBox[bufff]] = 100; //set a constant not zero and more than all of the numBox
//                                }
//                                //TODO this else if is doing exactly the same code as above, remove it
//                                else if (distanceBox[i][jBox[bufff]] < distanceBox[i][maxBoxDisOutNum[bufff]]) //always have two boxes match this condition at the same time, choice one of them
//                                {
//                                    minRectCoorX[robNum] = std::min(rect_coord[jBox[bufff]].tl().x, minRectCoorX[robNum]);
//                                    minRectCoorY[robNum] = std::min(rect_coord[jBox[bufff]].tl().y, minRectCoorY[robNum]);
//                                    maxRectCoorX[robNum] = std::max(rect_coord[jBox[bufff]].br().x, maxRectCoorX[robNum]);
//                                    maxRectCoorY[robNum] = std::max(rect_coord[jBox[bufff]].br().y, maxRectCoorY[robNum]);
//                                    numBox[jBox[bufff]] = 100; //set a constant not zero and more than all of the numBox
//                                }
//                                else
//                                {
//                                    minRectCoorX[robNum] = std::min(rect_coord[maxBoxDisOutNum[bufff]].tl().x, minRectCoorX[robNum]);
//                                    minRectCoorY[robNum] = std::min(rect_coord[maxBoxDisOutNum[bufff]].tl().y, minRectCoorY[robNum]);
//                                    maxRectCoorX[robNum] = std::max(rect_coord[maxBoxDisOutNum[bufff]].br().x, maxRectCoorX[robNum]);
//                                    maxRectCoorY[robNum] = std::max(rect_coord[maxBoxDisOutNum[bufff]].br().y, maxRectCoorY[robNum]);
//                                    numBox[maxBoxDisOutNum[bufff]] = 100;
//                                    delNum ++;
//                                }
//                            }
//                            lastnum = lastnum + delNum; //plus for the cancelled more one
//                            bufnum = bufnum - delNum;
//                        }
//                        else //compare center box and another one box, when bufnum = 1
//                        {
//                            if (maxBoxDisOut[jBox[0]] < 6.2 * rectBoxHeight) //the length of robot 9.4
//                            {
//                                minRectCoorX[robNum] = std::min(rect_coord[jBox[0]].tl().x, minRectCoorX[robNum]);
//                                minRectCoorY[robNum] = std::min(rect_coord[jBox[0]].tl().y, minRectCoorY[robNum]);
//                                maxRectCoorX[robNum] = std::max(rect_coord[jBox[0]].br().x, maxRectCoorX[robNum]);
//                                maxRectCoorY[robNum] = std::max(rect_coord[jBox[0]].br().y, maxRectCoorY[robNum]);
//                                numBox[jBox[0]] = 100; //set a constant not zero and more than all of the numBox
//                            }
//                            else //just one center to rest
//                            {
//                                robNum --;
//                            }
//                        }
//                    }
//                }
//            }
//        }
//    }
//
//    // calculate the angle
//    if (std::isnan(angle) and robNum == 0)
//    {
//        // init first angle
//        angle = atan(image.cols / static_cast<double>(image.rows)) * 180.0 / M_PI;
//    }
//    else
//    {
//        for (int i = 0; i < robNum; i++)
//        {
//            const int robCenterCoorX = 2*(minRectCoorX[i] + maxRectCoorX[i]);
//            const int robCenterCoorY = 2*(minRectCoorY[i] + maxRectCoorY[i]);
//            char textRobCenterCoor[64], textDistance[64];
//
//            if (show_image) {
//                cv::rectangle(raw_image, cv::Point(shrink_factor*minRectCoorX[i],shrink_factor*minRectCoorY[i]), cv::Point(shrink_factor*maxRectCoorX[i],shrink_factor*maxRectCoorY[i]), cv::Scalar(0,255,0),1);
//                cv::circle(raw_image, cv::Point(robCenterCoorX,robCenterCoorY),3, cv::Scalar(0,255,0),4);
//
//                std::snprintf(textRobCenterCoor, sizeof(textRobCenterCoor), "(%d,%d)", robCenterCoorX, robCenterCoorY);
//                cv::putText(raw_image, textRobCenterCoor, cv::Point(robCenterCoorX + 10, robCenterCoorY + 3),
//                        cv::FONT_HERSHEY_DUPLEX, 0.4, cv::Scalar(0, 255, 0), 1);
//            }
//
//            const int leftLine = raw_image.cols / 2;
//            const int rightLine = raw_image.cols / 2;
//            if (robCenterCoorX < leftLine)
//            {
//                double distance = robCenterCoorX - leftLine;
//                angle = std::atan(distance/robCenterCoorY) * 180.0 / M_PI;
//                if (show_image) {
//                    std::snprintf(textDistance, sizeof(textDistance), "L:%f Angle: %f", distance, angle);
//                    cv::putText(raw_image, textDistance, cv::Point(0.0 * raw_image.cols, 15), cv::FONT_HERSHEY_DUPLEX, 0.5,
//                            cv::Scalar(0, 255, 0), 1);
//                }
//            }
//
//            if (robCenterCoorX > rightLine)
//            {
//                double distance = robCenterCoorX - rightLine;
//                angle = std::atan(distance/robCenterCoorY) * 180.0 / M_PI;
//                if (show_image) {
//                    std::snprintf(textDistance, sizeof(textDistance), "R:%f Angle: %f", distance, angle);
//                    cv::putText(raw_image, textDistance, cv::Point(0.5 * raw_image.cols, 15), cv::FONT_HERSHEY_DUPLEX, 0.5,
//                            cv::Scalar(0, 255, 0), 1);
//                }
//            }
//
//            if (show_image) {
//                cv::line(raw_image, cv::Point(shrink_factor * minRectCoorX[i], shrink_factor * minRectCoorY[i]),
//                         cv::Point(shrink_factor * maxRectCoorX[i], shrink_factor * maxRectCoorY[i]), cv::Scalar(0, 255, 0), 1);
//                cv::line(raw_image, cv::Point(shrink_factor * minRectCoorX[i], shrink_factor * maxRectCoorY[i]),
//                         cv::Point(shrink_factor * maxRectCoorX[i], shrink_factor * minRectCoorY[i]), cv::Scalar(0, 255, 0), 1);
//                cv::line(raw_image, cv::Point(leftLine, 0), cv::Point(leftLine, raw_image.rows), cv::Scalar(0, 255, 0), 1);
//                cv::line(raw_image, cv::Point(rightLine, 0), cv::Point(rightLine, raw_image.rows), cv::Scalar(0, 255, 0), 1);
//            }
//        }
//    }
//
//
//    if (robNum == 0 and show_image) // no robots in the field of view
//    {
//        // show image if no robot is detected
//        char textDistance[64];
//        float text_pos;
//        if (angle < 0) text_pos = 0.0;
//        else text_pos = 0.5;
//        std::snprintf(textDistance, sizeof(textDistance), "Angle: %f", angle);
//        std::snprintf(textDistance, sizeof(textDistance), "Angle: %f", angle);
//        cv::putText(raw_image, textDistance, cv::Point(text_pos * raw_image.cols, 15), cv::FONT_HERSHEY_DUPLEX, 0.5,
//                    cv::Scalar(255, 0, 0), 1);
//    }
//
//    assert(not std::isnan(angle));
//
//    if (show_image) {
//        cv::imshow("revolve-controller", raw_image);
//        cv::waitKey(5);
//    }
//    return angle;
//}
